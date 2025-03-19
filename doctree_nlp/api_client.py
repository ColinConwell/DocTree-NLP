"""
Notion API client implementation with enhanced content handling.
"""

import logging
import os
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union, Literal
from tqdm.auto import tqdm

from .structure import Document, Block
from .caching import CacheManager
from .rate_limiter import RateLimiter
from .env_loader import find_notion_token
from .defaults import get_default

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Notion Client ----------------------------------------------------------------


class NotionClient:
    """Client for interacting with Notion API with enhanced content handling."""

    BASE_URL = "https://api.notion.com/v1"
    
    def __init__(
        self,
        token: Union[str, Literal["auto"]] = None,
        cache_enabled: bool = None,
        cache_dir: str = None,
        max_cache_age_days: Optional[int] = None,
        rate_limit: int = None,
    ):
        """
        Initialize the Notion client.

        Args:
            token: Notion API integration token or "auto" to auto-discover token
                  If "auto" is specified, the token will be searched in:
                  1. Environment variables (NOTION_API_TOKEN)
                  2. .env files in current directory
                  3. .env files in parent directories (up to depth 2)
                  4. User input (console or Jupyter widget)
            cache_enabled: Whether to use caching
            cache_dir: Directory to store cache files
            max_cache_age_days: Maximum age of cache entries in days (None for no expiry)
            rate_limit: Maximum number of requests per second
        
        Raises:
            AuthenticationError: If token is "auto" and no token could be found
        """
        # Get default values from defaults system
        auto_token = get_default('api.auto_token', 'auto')
        self.api_version = get_default('api.version', '2022-06-28')
        
        # Use provided values or defaults
        token = token if token is not None else auto_token
        self.cache_enabled = cache_enabled if cache_enabled is not None else get_default('cache.enabled', True)
        cache_dir = cache_dir if cache_dir is not None else get_default('cache.directory', 'cache')
        max_cache_age_days = max_cache_age_days if max_cache_age_days is not None else get_default('cache.max_age_days', None)
        rate_limit = rate_limit if rate_limit is not None else get_default('api.rate_limit', 3)
        
        # Handle token discovery
        if token == auto_token:
            discovered_token = find_notion_token()
            if discovered_token is None:
                raise AuthenticationError(
                    "Could not auto-discover Notion API token. "
                    "Please provide a token explicitly or set the NOTION_API_TOKEN environment variable."
                )
            self.token = discovered_token
            logger.info("Using auto-discovered Notion API token")
        else:
            self.token = token
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.api_version,
            "Content-Type": "application/json",
        }

        # Initialize cache manager if enabled
        if self.cache_enabled:
            self.cache_manager = CacheManager(
                api_token=self.token,  # Pass token to create API-specific cache
                cache_dir=cache_dir,
                max_age_days=max_cache_age_days,
            )

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit,
            time_window=1.0,  # 1 second window for rate limiting
        )

    def authenticate(self) -> bool:
        """
        Verify authentication token.

        Returns:
            bool: True if authentication successful

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            if not self.token or self.token == "fake_token":
                raise AuthenticationError("Invalid authentication token")

            # Apply rate limiting
            self.rate_limiter.wait_if_needed()

            response = requests.get(f"{self.BASE_URL}/users/me", headers=self.headers)
            if response.status_code == 401:
                raise AuthenticationError("Invalid authentication token")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def list_documents(self, use_cache: bool = None) -> List[Document]:
        """
        List available documents.

        Args:
            use_cache: Whether to use cache for this request (overrides instance setting)

        Returns:
            List[Document]: List of available documents
        """
        # Determine whether to use cache for this request
        should_use_cache = self.cache_enabled if use_cache is None else use_cache

        # Check cache first if enabled
        if should_use_cache and hasattr(self, "cache_manager"):
            cached_docs = self.cache_manager.get_cached_document_list()
            if cached_docs is not None:
                logger.debug("Using cached document list")
                return cached_docs

        try:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()

            response = requests.post(
                f"{self.BASE_URL}/search",
                headers=self.headers,
                json={"filter": {"property": "object", "value": "page"}},
            )

            if response.status_code != 200:
                logger.error(f"Failed to list documents: {response.text}")
                return (
                    []
                )  # Return empty list instead of raising error for Streamlit demo

            results = response.json().get("results", [])
            documents = []

            for result in tqdm(results, desc="Processing document list", unit="doc"):
                try:
                    title = self._extract_title(result)
                    doc = Document(
                        id=result["id"],
                        title=title or "Untitled",
                        created_time=datetime.fromisoformat(
                            result["created_time"].replace("Z", "+00:00")
                        ),
                        last_edited_time=datetime.fromisoformat(
                            result["last_edited_time"].replace("Z", "+00:00")
                        ),
                        last_fetched=datetime.now(),
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.error(
                        f"Error processing document {result.get('id')}: {str(e)}"
                    )
                    continue

            # Update cache if enabled
            if should_use_cache and hasattr(self, "cache_manager") and documents:
                self.cache_manager.cache_document_list(documents)

            return documents

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list documents: {str(e)}")
            return []  # Return empty list instead of raising error

    def _extract_title(self, result: Dict[str, Any]) -> str:
        """Extract title from document result."""
        try:
            if "properties" not in result or "title" not in result["properties"]:
                return "Untitled"

            title_parts = result["properties"]["title"]
            if isinstance(title_parts, list):
                return "".join(
                    part.get("text", {}).get("content", "")
                    for part in title_parts
                    if isinstance(part, dict)
                )
            elif isinstance(title_parts, dict) and "title" in title_parts:
                return "".join(
                    part.get("text", {}).get("content", "")
                    for part in title_parts["title"]
                    if isinstance(part, dict)
                )
            return "Untitled"
        except Exception as e:
            logger.error(f"Error extracting title: {str(e)}")
            return "Untitled"

    def get_document(self, document_id: str, use_cache: bool = None) -> Document:
        """
        Get a document with all its content.

        Args:
            document_id: ID of the document to fetch
            use_cache: Whether to use cache for this request (overrides instance setting)

        Returns:
            Document: A Document instance with metadata and blocks
            
        Usage:
            document = client.get_document(document_id)
        """
        metadata, blocks = self.get_document_content(document_id, use_cache)
        
        if metadata:
            # Create a full Document instance with blocks
            document = Document(
                id=metadata.id,
                title=metadata.title,
                created_time=metadata.created_time,
                last_edited_time=metadata.last_edited_time,
                last_fetched=metadata.last_fetched,
                etag=metadata.etag,
                blocks=blocks
            )
            return document
        else:
            # Return an empty document if metadata couldn't be fetched
            return Document(
                id=document_id,
                title="Unknown Document",
                created_time=datetime.now(),
                last_edited_time=datetime.now(),
                last_fetched=datetime.now(),
                blocks=blocks
            )
    
    def get_document_content(
        self, document_id: str, use_cache: bool = None
    ) -> Tuple[Document, List[Block]]:
        """
        Get content of a document with enhanced block handling.

        Args:
            document_id: ID of the document to fetch
            use_cache: Whether to use cache for this request (overrides instance setting)

        Returns:
            Tuple[Document, List[Block]]: A tuple containing:
                - metadata (Document): Document metadata including title, creation time, and edit time
                - blocks (List[Block]): List of content blocks from the document

        Usage:
            metadata, blocks = client.get_document_content(document_id)
        """
        # Determine whether to use cache for this request
        should_use_cache = self.cache_enabled if use_cache is None else use_cache

        # Get document metadata first to check last_edited_time
        document = self._get_document_metadata(document_id)

        # Check cache first if enabled
        if should_use_cache and hasattr(self, "cache_manager") and document:
            if self.cache_manager.is_document_cached(
                document_id, document.last_edited_time
            ):
                cached_doc, cached_blocks = self.cache_manager.get_cached_document(
                    document_id
                )
                if cached_doc and cached_blocks:
                    logger.debug(f"Using cached content for document {document_id}")
                    return cached_doc, cached_blocks

        # If not cached or cache disabled, fetch from API
        blocks = []
        has_more = True
        cursor = None

        try:
            while has_more:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()

                url = f"{self.BASE_URL}/blocks/{document_id}/children"
                params = {"page_size": 100}
                if cursor:
                    params["start_cursor"] = cursor

                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code != 200:
                    logger.error(f"Failed to get document content: {response.text}")
                    break  # Break instead of raising error

                data = response.json()
                results = data.get("results", [])

                for result in tqdm(
                    results,
                    desc="Processing document blocks",
                    unit="block",
                    leave=False,
                ):
                    try:
                        block_type = result.get("type", "")
                        content = self._extract_block_content(result, block_type)

                        if content:  # Only create block if content was extracted
                            block = Block(
                                id=result["id"],
                                type=block_type,
                                content=content,
                                has_children=result.get("has_children", False),
                                indent_level=0,
                            )
                            blocks.append(block)

                            # Handle nested blocks if present
                            if block.has_children:
                                try:
                                    # Apply rate limiting for nested request
                                    self.rate_limiter.wait_if_needed()

                                    # Recursively fetch nested blocks
                                    _, nested_blocks = self._get_nested_blocks(block.id)
                                    for nested_block in nested_blocks:
                                        nested_block.indent_level = (
                                            block.indent_level + 1
                                        )
                                        blocks.append(nested_block)
                                except Exception as e:
                                    logger.error(
                                        f"Error processing nested blocks: {str(e)}"
                                    )
                                    continue
                    except Exception as e:
                        logger.error(
                            f"Error processing block {result.get('id')}: {str(e)}"
                        )
                        continue

                has_more = data.get("has_more", False)
                cursor = data.get("next_cursor")

            # Update document with fetched time
            if document:
                document.last_fetched = datetime.now()

            # Update cache if enabled
            if (
                should_use_cache
                and hasattr(self, "cache_manager")
                and document
                and blocks
            ):
                self.cache_manager.cache_document(document_id, document, blocks)

            return document, blocks

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get document content: {str(e)}")
            return document, []  # Return empty list instead of raising error

    def _get_nested_blocks(self, block_id: str) -> Tuple[None, List[Block]]:
        """
        Helper method to get nested blocks.
        This is separated to avoid recursive caching issues.
        """
        # This is essentially the same as get_document_content but without caching
        blocks = []
        has_more = True
        cursor = None

        try:
            while has_more:
                # Apply rate limiting
                self.rate_limiter.wait_if_needed()

                url = f"{self.BASE_URL}/blocks/{block_id}/children"
                params = {"page_size": 100}
                if cursor:
                    params["start_cursor"] = cursor

                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code != 200:
                    logger.error(f"Failed to get nested blocks: {response.text}")
                    break

                data = response.json()
                results = data.get("results", [])

                for result in tqdm(
                    results, desc="Processing nested blocks", unit="block", leave=False
                ):
                    try:
                        block_type = result.get("type", "")
                        content = self._extract_block_content(result, block_type)

                        if content:  # Only create block if content was extracted
                            block = Block(
                                id=result["id"],
                                type=block_type,
                                content=content,
                                has_children=result.get("has_children", False),
                                indent_level=0,
                            )
                            blocks.append(block)

                            # Handle nested blocks if present
                            if block.has_children:
                                try:
                                    # Apply rate limiting for nested request
                                    self.rate_limiter.wait_if_needed()

                                    # Recursively fetch nested blocks
                                    _, nested_blocks = self._get_nested_blocks(block.id)
                                    for nested_block in nested_blocks:
                                        nested_block.indent_level = (
                                            block.indent_level + 1
                                        )
                                        blocks.append(nested_block)
                                except Exception as e:
                                    logger.error(
                                        f"Error processing nested blocks: {str(e)}"
                                    )
                                    continue
                    except Exception as e:
                        logger.error(
                            f"Error processing block {result.get('id')}: {str(e)}"
                        )
                        continue

                has_more = data.get("has_more", False)
                cursor = data.get("next_cursor")

            return None, blocks

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get nested blocks: {str(e)}")
            return None, []

    def _get_document_metadata(self, document_id: str) -> Optional[Document]:
        """
        Get document metadata.

        Args:
            document_id: Document ID

        Returns:
            Optional[Document]: Document metadata or None if not found
        """
        try:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()

            url = f"{self.BASE_URL}/pages/{document_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                logger.error(f"Failed to get document metadata: {response.text}")
                return None

            result = response.json()
            title = self._extract_title(result)

            return Document(
                id=result["id"],
                title=title or "Untitled",
                created_time=datetime.fromisoformat(
                    result["created_time"].replace("Z", "+00:00")
                ),
                last_edited_time=datetime.fromisoformat(
                    result["last_edited_time"].replace("Z", "+00:00")
                ),
                last_fetched=datetime.now(),
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get document metadata: {str(e)}")
            return None

    def _extract_block_content(self, block: Dict[str, Any], block_type: str) -> str:
        """
        Extract content from a block with enhanced handling of different block types.

        Args:
            block: Block data from API
            block_type: Type of the block

        Returns:
            str: Extracted content
        """
        try:
            block_data = block.get(block_type, {})

            # Handle both rich_text and text array formats
            text_array = block_data.get("rich_text", block_data.get("text", []))

            if not text_array:
                return ""

            if block_type == "code":
                language = block_data.get("language", "")
                code_text = self._extract_rich_text(text_array)
                return f"{language}\n{code_text}" if code_text else ""

            elif block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
                return self._extract_rich_text(text_array)

            elif block_type == "bulleted_list_item":
                content = self._extract_rich_text(text_array)
                return f"• {content}" if content else ""

            elif block_type == "numbered_list_item":
                return self._extract_rich_text(text_array)

            elif block_type == "to_do":
                checked = "✓ " if block_data.get("checked", False) else "□ "
                content = self._extract_rich_text(text_array)
                return f"{checked}{content}" if content else ""

            elif block_type == "quote":
                content = self._extract_rich_text(text_array)
                return f"> {content}" if content else ""

            return self._extract_rich_text(text_array)

        except Exception as e:
            logger.error(f"Error extracting content from {block_type} block: {str(e)}")
            return ""

    def _extract_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract text content from rich_text array."""
        try:
            content = []
            for text in rich_text:
                if not isinstance(text, dict):
                    continue

                # Try plain_text first, then fallback to text.content
                text_content = text.get("plain_text")
                if text_content is None:
                    text_content = text.get("text", {}).get("content")

                if text_content:
                    content.append(text_content)

            return "".join(content)

        except Exception as e:
            logger.error(f"Error extracting rich text: {str(e)}")
            return ""

    # Cache control methods --------------------------------------------------------

    def clear_cache(self):
        """
        Clear all cached data.

        Raises:
            CacheError: If cache clearing fails or caching is disabled
        """
        if not self.cache_enabled or not hasattr(self, "cache_manager"):
            raise CacheError("Caching is disabled")

        try:
            self.cache_manager.clear_cache()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            raise CacheError(f"Failed to clear cache: {str(e)}")

    def clear_document_cache(self, document_id: str):
        """
        Clear cache for a specific document.

        Args:
            document_id: ID of the document to clear from cache

        Raises:
            CacheError: If cache clearing fails or caching is disabled
        """
        if not self.cache_enabled or not hasattr(self, "cache_manager"):
            raise CacheError("Caching is disabled")

        try:
            self.cache_manager.clear_document_cache(document_id)
            logger.info(f"Cache cleared for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to clear document cache: {str(e)}")
            raise CacheError(f"Failed to clear document cache: {str(e)}")

    def set_cache_dir(self, cache_dir: str):
        """
        Change the cache directory.

        Args:
            cache_dir: New cache directory path

        Raises:
            CacheError: If changing cache directory fails or caching is disabled
        """
        if not self.cache_enabled:
            raise CacheError("Caching is disabled")

        try:
            # Calculate max_age_days from seconds, handling None case
            max_age_days = None
            if (
                hasattr(self.cache_manager, "max_age_seconds")
                and self.cache_manager.max_age_seconds is not None
            ):
                max_age_days = self.cache_manager.max_age_seconds / (24 * 60 * 60)

            self.cache_manager = CacheManager(
                api_token=self.token, cache_dir=cache_dir, max_age_days=max_age_days
            )
            logger.info(f"Cache directory changed to {cache_dir}")
        except Exception as e:
            logger.error(f"Failed to change cache directory: {str(e)}")
            raise CacheError(f"Failed to change cache directory: {str(e)}")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the cache.

        Returns:
            Dict: Cache information

        Raises:
            CacheError: If getting cache info fails or caching is disabled
        """
        if not self.cache_enabled or not hasattr(self, "cache_manager"):
            raise CacheError("Caching is disabled")

        try:
            cache_dir = self.cache_manager.cache_dir
            max_age_days = self.cache_manager.max_age_seconds / (24 * 60 * 60)

            # Count cache files
            cache_files = list(cache_dir.glob("*.json"))
            num_files = len(cache_files)

            # Get total cache size
            total_size = sum(f.stat().st_size for f in cache_files)

            # Calculate max_age_days
            max_age_days = None
            if (
                hasattr(self.cache_manager, "max_age_seconds")
                and self.cache_manager.max_age_seconds is not None
            ):
                max_age_days = self.cache_manager.max_age_seconds / (24 * 60 * 60)

            return {
                "enabled": self.cache_enabled,
                "cache_dir": str(cache_dir),
                "max_age_days": max_age_days,
                "api_specific": True,  # Flag indicating cache is API-key specific
                "num_files": num_files,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
            }
        except Exception as e:
            logger.error(f"Failed to get cache info: {str(e)}")
            raise CacheError(f"Failed to get cache info: {str(e)}")

    def get_all_available_data(
        self, document_id: str, use_cache: bool = None
    ) -> Dict[str, Any]:
        """
        Get all raw data available from the Notion API for a specific document.

        This function provides a comprehensive dictionary of all information
        available from the Notion API about a document, including metadata,
        properties, content, children blocks with their original formats,
        and any other available attributes.

        Args:
            document_id: ID of the document to fetch
            use_cache: Whether to use cache for this request (overrides instance setting)

        Returns:
            Dict[str, Any]: Dictionary containing all available data from the API

        Example:
            raw_data = client.get_all_available_data(document_id)
            # Access specific data points
            page_properties = raw_data['page_data']['properties']
            all_blocks = raw_data['block_data']
            block_types = [block['type'] for block in all_blocks]
        """
        # Determine whether to use cache for this request
        should_use_cache = self.cache_enabled if use_cache is None else use_cache

        # Check cache first if enabled
        if should_use_cache and hasattr(self, "cache_manager"):
            cached_raw_data = self.cache_manager.get_cached_data(f"{document_id}_raw")
            if cached_raw_data is not None:
                logger.debug(f"Using cached raw data for document {document_id}")
                return cached_raw_data

        # Prepare response dictionary
        raw_data = {
            "page_data": {},
            "block_data": [],
            "collection_data": {},
            "user_data": {},
            "comments_data": [],
        }

        try:
            # STEP 1: Get page metadata
            logger.info(f"Fetching page data for document {document_id}")
            self.rate_limiter.wait_if_needed()
            url = f"{self.BASE_URL}/pages/{document_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                raw_data["page_data"] = response.json()
            else:
                logger.error(f"Failed to get page data: {response.text}")
                raw_data["errors"] = {
                    "page_data": f"API Error: {response.status_code} - {response.text}"
                }

            # STEP 2: Get content blocks
            blocks = []
            has_more = True
            cursor = None

            logger.info(f"Fetching block content for document {document_id}")
            while has_more:
                self.rate_limiter.wait_if_needed()
                url = f"{self.BASE_URL}/blocks/{document_id}/children"
                params = {"page_size": 100}
                if cursor:
                    params["start_cursor"] = cursor

                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code == 200:
                    data = response.json()
                    blocks.extend(data.get("results", []))
                    has_more = data.get("has_more", False)
                    cursor = data.get("next_cursor")
                else:
                    logger.error(f"Failed to get blocks: {response.text}")
                    raw_data["errors"] = raw_data.get("errors", {})
                    raw_data["errors"][
                        "block_data"
                    ] = f"API Error: {response.status_code} - {response.text}"
                    break

            raw_data["block_data"] = blocks

            # STEP 3: Get nested blocks for each block that has children
            for idx, block in enumerate(
                tqdm(blocks, desc="Fetching nested blocks", unit="block")
            ):
                if block.get("has_children", False):
                    block_id = block.get("id")
                    nested_blocks = self._get_all_nested_blocks(block_id)
                    raw_data["block_data"][idx]["children"] = nested_blocks

            # STEP 4: Get comments if available
            if "comments" in raw_data["page_data"].get("url", ""):
                try:
                    self.rate_limiter.wait_if_needed()
                    url = f"{self.BASE_URL}/comments?block_id={document_id}"
                    response = requests.get(url, headers=self.headers)

                    if response.status_code == 200:
                        raw_data["comments_data"] = response.json().get("results", [])
                except Exception as e:
                    logger.error(f"Error fetching comments: {str(e)}")
                    raw_data["errors"] = raw_data.get("errors", {})
                    raw_data["errors"]["comments_data"] = str(e)

            # STEP 5: Get database information if this is a database page
            if "database_id" in raw_data["page_data"]:
                try:
                    database_id = raw_data["page_data"]["database_id"]
                    self.rate_limiter.wait_if_needed()
                    url = f"{self.BASE_URL}/databases/{database_id}"
                    response = requests.get(url, headers=self.headers)

                    if response.status_code == 200:
                        raw_data["collection_data"] = response.json()
                except Exception as e:
                    logger.error(f"Error fetching database information: {str(e)}")
                    raw_data["errors"] = raw_data.get("errors", {})
                    raw_data["errors"]["collection_data"] = str(e)

            # Add metadata about the fetch operation
            raw_data["_meta"] = {
                "document_id": document_id,
                "fetched_at": datetime.now().isoformat(),
                "api_version": self.API_VERSION,
            }

            # Cache the raw data if caching is enabled
            if should_use_cache and hasattr(self, "cache_manager"):
                self.cache_manager.cache_raw_data(f"{document_id}_raw", raw_data)

            return raw_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get document raw data: {str(e)}")
            raw_data["errors"] = raw_data.get("errors", {})
            raw_data["errors"]["request"] = str(e)
            return raw_data

    def _get_all_nested_blocks(self, block_id: str) -> List[Dict[str, Any]]:
        """
        Helper method to get all nested blocks with their original API format.

        Args:
            block_id: ID of the parent block

        Returns:
            List[Dict[str, Any]]: List of nested blocks with their original format
        """
        blocks = []
        has_more = True
        cursor = None

        try:
            while has_more:
                self.rate_limiter.wait_if_needed()
                url = f"{self.BASE_URL}/blocks/{block_id}/children"
                params = {"page_size": 100}
                if cursor:
                    params["start_cursor"] = cursor

                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code != 200:
                    logger.error(f"Failed to get nested blocks: {response.text}")
                    break

                data = response.json()
                results = data.get("results", [])
                blocks.extend(results)

                # Recursively get children for each nested block
                for idx, nested_block in enumerate(results):
                    if nested_block.get("has_children", False):
                        nested_id = nested_block.get("id")
                        children = self._get_all_nested_blocks(nested_id)
                        blocks[idx]["children"] = children

                has_more = data.get("has_more", False)
                cursor = data.get("next_cursor")

            return blocks

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get nested blocks: {str(e)}")
            return blocks


# Exceptions ------------------------------------------------------------


class NotionNLPError(Exception):
    """Base exception for Notion NLP library."""
    pass

# Alias for future transition
DocTreeError = NotionNLPError


class AuthenticationError(NotionNLPError):
    """Raised when authentication fails."""

    pass


class CacheError(NotionNLPError):
    """Raised when cache operations fail."""

    pass


# Other Clients -------------------------------------------------------


class ObsidianClient:
    """Client for reading and processing Obsidian vaults."""
    
    def __init__(
        self,
        vault_path: str,
        cache_enabled: bool = None,
        cache_dir: str = None,
        max_cache_age_days: Optional[int] = None,
    ):
        """
        Initialize the Obsidian client.
        
        Args:
            vault_path: Path to the Obsidian vault directory
            cache_enabled: Whether to use caching
            cache_dir: Directory to store cache files
            max_cache_age_days: Maximum age of cache entries in days (None for no expiry)
        """
        # Use provided values or defaults
        self.vault_path = Path(vault_path)
        self.cache_enabled = cache_enabled if cache_enabled is not None else get_default('cache.enabled', True)
        cache_dir = cache_dir if cache_dir is not None else get_default('cache.directory', 'cache')
        max_cache_age_days = max_cache_age_days if max_cache_age_days is not None else get_default('cache.max_age_days', None)
        
        # Validate vault path
        if not self.vault_path.exists() or not self.vault_path.is_dir():
            raise ValueError(f"Obsidian vault path does not exist or is not a directory: {vault_path}")
        
        # Initialize cache manager if enabled
        if self.cache_enabled:
            self.cache_manager = CacheManager(
                api_token=f"obsidian-{self.vault_path.name}",  # Create vault-specific cache
                cache_dir=cache_dir,
                max_age_days=max_cache_age_days,
                source_dir=get_default('cache.sources.internal', 'internal'),  # Use internal cache source
            )
            
        logger.info(f"Initialized Obsidian client for vault: {self.vault_path}")
    
    def list_documents(self, use_cache: bool = None) -> List[Document]:
        """
        List available markdown documents in the vault.
        
        Args:
            use_cache: Whether to use cache for this request (overrides instance setting)
            
        Returns:
            List[Document]: List of available documents
        """
        # Placeholder implementation - will be expanded in future
        should_use_cache = self.cache_enabled if use_cache is None else use_cache
        
        # Check cache first if enabled
        if should_use_cache and hasattr(self, "cache_manager"):
            cached_docs = self.cache_manager.get_cached_document_list()
            if cached_docs is not None:
                logger.debug("Using cached document list")
                return cached_docs
        
        # Find all markdown files
        markdown_files = list(self.vault_path.glob("**/*.md"))
        documents = []
        
        for md_file in tqdm(markdown_files, desc="Processing Obsidian files", unit="file"):
            # Get file stats
            stats = md_file.stat()
            created_time = datetime.fromtimestamp(stats.st_ctime)
            modified_time = datetime.fromtimestamp(stats.st_mtime)
            
            # Extract title from filename or first heading in the file
            title = md_file.stem  # Default to filename without extension
            
            # Create document
            doc = Document(
                id=str(md_file.relative_to(self.vault_path)),
                title=title,
                created_time=created_time,
                last_edited_time=modified_time,
                last_fetched=datetime.now(),
                source_id=f"obsidian-{self.vault_path.name}"
            )
            documents.append(doc)
        
        # Update cache if enabled
        if should_use_cache and hasattr(self, "cache_manager") and documents:
            self.cache_manager.cache_document_list(documents)
            
        return documents
    
    def get_document(self, document_id: str, use_cache: bool = None) -> Document:
        """
        Get a document with all its content.
        
        Args:
            document_id: ID (relative path) of the document to fetch
            use_cache: Whether to use cache for this request (overrides instance setting)
            
        Returns:
            Document: A Document instance with metadata and blocks
        """
        # This is a placeholder implementation
        metadata, blocks = self.get_document_content(document_id, use_cache)
        
        if metadata:
            document = Document(
                id=metadata.id,
                title=metadata.title,
                created_time=metadata.created_time,
                last_edited_time=metadata.last_edited_time,
                last_fetched=metadata.last_fetched,
                etag=metadata.etag,
                blocks=blocks
            )
            return document
        else:
            # Return an empty document if metadata couldn't be fetched
            return Document(
                id=document_id,
                title="Unknown Document",
                created_time=datetime.now(),
                last_edited_time=datetime.now(),
                last_fetched=datetime.now(),
                blocks=blocks
            )
    
    def get_document_content(
        self, document_id: str, use_cache: bool = None
    ) -> Tuple[Document, List[Block]]:
        """
        Get content of a document with enhanced block handling.
        
        Args:
            document_id: ID (relative path) of the document to fetch
            use_cache: Whether to use cache for this request (overrides instance setting)
            
        Returns:
            Tuple[Document, List[Block]]: A tuple containing metadata and blocks
        """
        # Implementation to be expanded in future
        # For now, return empty metadata and blocks list
        logger.info(f"Obsidian content fetching not yet implemented for document: {document_id}")
        
        # Create basic document metadata
        doc = Document(
            id=document_id,
            title=Path(document_id).stem,
            created_time=datetime.now(),
            last_edited_time=datetime.now(),
            last_fetched=datetime.now(),
            source_id=f"obsidian-{self.vault_path.name}"
        )
        
        return doc, []


class LocalSource:
    """Client for processing local directories of markdown files."""
    
    def __init__(
        self,
        directory_path: str = None,
        file_pattern: str = None,
        cache_enabled: bool = None,
        cache_dir: str = None,
        max_cache_age_days: Optional[int] = None,
        file_types: List[str] = None,
        source_as_single_doctree: bool = False,
        encoding: str = None,
    ):
        """
        Initialize the local source client.
        
        Args:
            directory_path: Path to the directory containing markdown files. If None, user will be prompted.
            file_pattern: Glob pattern to match files (default from settings)
            cache_enabled: Whether to use caching
            cache_dir: Directory to store cache files
            max_cache_age_days: Maximum age of cache entries in days (None for no expiry)
            file_types: List of file extensions to process (default: [".md"])
            source_as_single_doctree: If True, all files are treated as a single document with hierarchy based on folders
            encoding: File encoding to use when reading files
        """
        # Use provided values or defaults
        self.file_pattern = file_pattern if file_pattern is not None else get_default('local.default_pattern', "**/*.md")
        self.cache_enabled = cache_enabled if cache_enabled is not None else get_default('cache.enabled', True)
        cache_dir = cache_dir if cache_dir is not None else get_default('cache.directory', 'cache')
        max_cache_age_days = max_cache_age_days if max_cache_age_days is not None else get_default('cache.max_age_days', None)
        self.encoding = encoding if encoding is not None else get_default('local.encoding', 'utf-8')
        self.file_types = file_types if file_types is not None else [".md"]
        self.source_as_single_doctree = source_as_single_doctree
        
        # If no directory path provided, prompt the user
        if directory_path is None:
            directory_path = self._prompt_directory_path()
        
        self.directory_path = Path(directory_path)
        
        # Validate directory path
        if not self.directory_path.exists() or not self.directory_path.is_dir():
            raise ValueError(f"Directory path does not exist or is not a directory: {directory_path}")
        
        # Initialize cache manager if enabled
        if self.cache_enabled:
            dir_hash = self.directory_path.name  # Use directory name as part of cache key
            self.cache_manager = CacheManager(
                api_token=f"local-{dir_hash}",
                cache_dir=cache_dir,
                max_age_days=max_cache_age_days,
                source_dir=get_default('cache.sources.local', 'local'),  # Use local cache source
            )
            
        logger.info(f"Initialized local source client for directory: {self.directory_path}")
    
    def _prompt_directory_path(self) -> str:
        """
        Prompt the user for a directory path.
        
        Returns:
            str: Directory path provided by the user
        """
        try:
            # First, try to use IPython widgets if in a Jupyter environment
            from IPython.display import display
            import ipywidgets as widgets
            
            # Create a text input widget
            text = widgets.Text(
                value='',
                placeholder='Enter directory path',
                description='Directory:',
                disabled=False
            )
            
            # Create a button widget
            button = widgets.Button(
                description='Confirm',
                disabled=False,
                button_style='success',
                tooltip='Click to confirm'
            )
            
            # Store the input value
            result = {'path': None}
            
            def on_button_clicked(b):
                result['path'] = text.value
                
            button.on_click(on_button_clicked)
            
            # Display the widgets
            display(text)
            display(button)
            
            # Wait for user input
            while result['path'] is None:
                import time
                time.sleep(0.1)
                
            return result['path']
            
        except (ImportError, ModuleNotFoundError):
            # Fall back to console input if not in Jupyter
            return input("Enter directory path for documents: ")
    
    def _get_file_pattern(self) -> str:
        """Get the appropriate glob pattern based on file types."""
        if self.file_pattern:
            return self.file_pattern
            
        patterns = []
        for ext in self.file_types:
            if not ext.startswith('.'):
                ext = f".{ext}"
            patterns.append(f"**/*{ext}")
            
        return "{" + ",".join(patterns) + "}" if len(patterns) > 1 else patterns[0]
    
    def list_documents(self, use_cache: bool = None) -> List[Document]:
        """
        List available documents in the directory.
        
        Args:
            use_cache: Whether to use cache for this request (overrides instance setting)
            
        Returns:
            List[Document]: List of available documents
        """
        should_use_cache = self.cache_enabled if use_cache is None else use_cache
        
        # Check cache first if enabled
        if should_use_cache and hasattr(self, "cache_manager"):
            cached_docs = self.cache_manager.get_cached_document_list()
            if cached_docs is not None:
                logger.debug("Using cached document list")
                return cached_docs
        
        # Find all matching files using either the pattern or file types
        files = list(self.directory_path.glob(self._get_file_pattern()))
        documents = []
        
        # If treating all files as a single document tree
        if self.source_as_single_doctree:
            # Create one document representing the entire directory
            stats = self.directory_path.stat()
            created_time = datetime.fromtimestamp(stats.st_ctime)
            
            # Find the most recent modification time among all files
            most_recent_time = created_time
            for file in files:
                modified_time = datetime.fromtimestamp(file.stat().st_mtime)
                if modified_time > most_recent_time:
                    most_recent_time = modified_time
            
            doc = Document(
                id="_combined_doctree",
                title=self.directory_path.name,
                created_time=created_time,
                last_edited_time=most_recent_time,
                last_fetched=datetime.now(),
                source_id=f"local-{self.directory_path.name}"
            )
            documents.append(doc)
        else:
            # Create a document for each file
            for file in tqdm(files, desc="Processing local files", unit="file"):
                # Get file stats
                stats = file.stat()
                created_time = datetime.fromtimestamp(stats.st_ctime)
                modified_time = datetime.fromtimestamp(stats.st_mtime)
                
                # Create document
                doc = Document(
                    id=str(file.relative_to(self.directory_path)),
                    title=file.stem,  # Use filename without extension as title
                    created_time=created_time,
                    last_edited_time=modified_time,
                    last_fetched=datetime.now(),
                    source_id=f"local-{self.directory_path.name}"
                )
                documents.append(doc)
        
        # Update cache if enabled
        if should_use_cache and hasattr(self, "cache_manager") and documents:
            self.cache_manager.cache_document_list(documents)
            
        return documents
    
    def get_document(self, document_id: str, use_cache: bool = None) -> Document:
        """
        Get a document with all its content.
        
        Args:
            document_id: ID (relative path) of the document to fetch
            use_cache: Whether to use cache for this request (overrides instance setting)
            
        Returns:
            Document: A Document instance with metadata and blocks
        """
        metadata, blocks = self.get_document_content(document_id, use_cache)
        
        if metadata:
            document = Document(
                id=metadata.id,
                title=metadata.title,
                created_time=metadata.created_time,
                last_edited_time=metadata.last_edited_time,
                last_fetched=metadata.last_fetched,
                etag=metadata.etag,
                source_id=metadata.source_id,
                blocks=blocks
            )
            # Build the document tree
            if blocks:
                document.build_tree()
            return document
        else:
            # Return an empty document if metadata couldn't be fetched
            return Document(
                id=document_id,
                title=Path(document_id).stem if document_id != "_combined_doctree" else self.directory_path.name,
                created_time=datetime.now(),
                last_edited_time=datetime.now(),
                last_fetched=datetime.now(),
                blocks=blocks
            )
    
    def get_document_content(
        self, document_id: str, use_cache: bool = None
    ) -> Tuple[Document, List[Block]]:
        """
        Get content of a document with enhanced block handling.
        
        Args:
            document_id: ID (relative path) of the document to fetch
            use_cache: Whether to use cache for this request (overrides instance setting)
            
        Returns:
            Tuple[Document, List[Block]]: A tuple containing metadata and blocks
        """
        should_use_cache = self.cache_enabled if use_cache is None else use_cache
        
        # Check if we're using the special combined document ID
        if document_id == "_combined_doctree" and self.source_as_single_doctree:
            return self._get_combined_content(use_cache=should_use_cache)
        
        # Check cache first if enabled
        if should_use_cache and hasattr(self, "cache_manager"):
            # Try to get from cache based on document_id and modification time
            file_path = self.directory_path / document_id
            if file_path.exists():
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if self.cache_manager.is_document_cached(document_id, modified_time):
                    cached_doc, cached_blocks = self.cache_manager.get_cached_document(document_id)
                    if cached_doc and cached_blocks:
                        logger.debug(f"Using cached content for document {document_id}")
                        return cached_doc, cached_blocks
        
        # File path for the document
        file_path = self.directory_path / document_id
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            logger.error(f"Document file not found: {file_path}")
            return None, []
        
        # Get file stats for metadata
        stats = file_path.stat()
        created_time = datetime.fromtimestamp(stats.st_ctime)
        modified_time = datetime.fromtimestamp(stats.st_mtime)
        
        # Create document metadata
        doc = Document(
            id=document_id,
            title=file_path.stem,
            created_time=created_time,
            last_edited_time=modified_time,
            last_fetched=datetime.now(),
            source_id=f"local-{self.directory_path.name}"
        )
        
        # Parse file content into blocks
        try:
            blocks = self._parse_file_to_blocks(file_path)
            
            # Update cache if enabled
            if should_use_cache and hasattr(self, "cache_manager"):
                self.cache_manager.cache_document(document_id, doc, blocks)
                
            return doc, blocks
            
        except Exception as e:
            logger.error(f"Error parsing document {document_id}: {str(e)}")
            return doc, []
    
    def _parse_file_to_blocks(self, file_path: Path) -> List[Block]:
        """
        Parse a file into blocks based on its type.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            List[Block]: List of parsed blocks
        """
        # Determine file type from extension
        file_ext = file_path.suffix.lower()
        
        # Read file content
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding as fallback
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                logger.warning(f"Used fallback encoding for {file_path}")
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {str(e)}")
                return []
        
        # Parse content based on file type
        if file_ext == '.md':
            return self._parse_markdown(content, file_path)
        elif file_ext == '.txt':
            return self._parse_text(content, file_path)
        else:
            # Default handling for unknown types
            return self._parse_text(content, file_path)
    
    def _parse_markdown(self, content: str, file_path: Path) -> List[Block]:
        """
        Parse markdown content into blocks.
        
        Args:
            content: The markdown content to parse
            file_path: Path to the source file (for block IDs)
            
        Returns:
            List[Block]: List of parsed blocks
        """
        blocks = []
        lines = content.split('\n')
        current_block = {'type': 'paragraph', 'content': [], 'indent': 0}
        block_id_counter = 1
        
        for line in lines:
            # Skip empty lines that are not part of a code block
            if not line.strip() and current_block['type'] != 'code':
                if current_block['content']:
                    # Finish the current block
                    blocks.append(Block(
                        id=f"{file_path.stem}_{block_id_counter}",
                        type=current_block['type'],
                        content='\n'.join(current_block['content']).strip(),
                        indent_level=current_block['indent']
                    ))
                    block_id_counter += 1
                    current_block = {'type': 'paragraph', 'content': [], 'indent': 0}
                continue
                
            # Check for headings (ATX style: # Heading)
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                # Finish the current block if any
                if current_block['content']:
                    blocks.append(Block(
                        id=f"{file_path.stem}_{block_id_counter}",
                        type=current_block['type'],
                        content='\n'.join(current_block['content']).strip(),
                        indent_level=current_block['indent']
                    ))
                    block_id_counter += 1
                
                # Create heading block
                heading_level = len(heading_match.group(1))
                blocks.append(Block(
                    id=f"{file_path.stem}_{block_id_counter}",
                    type=f"heading_{heading_level}",
                    content=heading_match.group(2).strip(),
                    indent_level=0
                ))
                block_id_counter += 1
                current_block = {'type': 'paragraph', 'content': [], 'indent': 0}
                continue
                
            # Check for bullet lists
            bullet_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
            if bullet_match:
                # Finish the current block if it's not a bullet list or has different indentation
                indent_level = len(bullet_match.group(1)) // 2
                if (current_block['type'] != 'bulleted_list_item' or 
                    current_block['indent'] != indent_level) and current_block['content']:
                    blocks.append(Block(
                        id=f"{file_path.stem}_{block_id_counter}",
                        type=current_block['type'],
                        content='\n'.join(current_block['content']).strip(),
                        indent_level=current_block['indent']
                    ))
                    block_id_counter += 1
                    
                # Start new bullet list item or continue existing one
                if current_block['type'] != 'bulleted_list_item' or current_block['indent'] != indent_level:
                    current_block = {'type': 'bulleted_list_item', 'content': [bullet_match.group(2)], 'indent': indent_level}
                else:
                    current_block['content'].append(bullet_match.group(2))
                continue
                
            # Check for numbered lists
            number_match = re.match(r'^(\s*)(\d+)[\.\)]\s+(.+)$', line)
            if number_match:
                # Finish the current block if it's not a numbered list or has different indentation
                indent_level = len(number_match.group(1)) // 2
                if (current_block['type'] != 'numbered_list_item' or 
                    current_block['indent'] != indent_level) and current_block['content']:
                    blocks.append(Block(
                        id=f"{file_path.stem}_{block_id_counter}",
                        type=current_block['type'],
                        content='\n'.join(current_block['content']).strip(),
                        indent_level=current_block['indent']
                    ))
                    block_id_counter += 1
                    
                # Start new numbered list item or continue existing one
                if current_block['type'] != 'numbered_list_item' or current_block['indent'] != indent_level:
                    current_block = {'type': 'numbered_list_item', 'content': [number_match.group(3)], 'indent': indent_level}
                else:
                    current_block['content'].append(number_match.group(3))
                continue
                
            # Check for code blocks (```lang)
            code_start_match = re.match(r'^```(\w*)$', line)
            if code_start_match and current_block['type'] != 'code':
                # Finish the current block if any
                if current_block['content']:
                    blocks.append(Block(
                        id=f"{file_path.stem}_{block_id_counter}",
                        type=current_block['type'],
                        content='\n'.join(current_block['content']).strip(),
                        indent_level=current_block['indent']
                    ))
                    block_id_counter += 1
                
                # Start code block
                lang = code_start_match.group(1) or "text"
                current_block = {'type': 'code', 'content': [lang], 'indent': 0}
                continue
            
            # Check for code block end
            if line.strip() == '```' and current_block['type'] == 'code':
                # Finish the code block
                blocks.append(Block(
                    id=f"{file_path.stem}_{block_id_counter}",
                    type='code',
                    content='\n'.join(current_block['content']),
                    indent_level=0
                ))
                block_id_counter += 1
                current_block = {'type': 'paragraph', 'content': [], 'indent': 0}
                continue
                
            # Check for block quotes
            quote_match = re.match(r'^>\s*(.*)$', line)
            if quote_match:
                # Finish the current block if it's not a quote
                if current_block['type'] != 'quote' and current_block['content']:
                    blocks.append(Block(
                        id=f"{file_path.stem}_{block_id_counter}",
                        type=current_block['type'],
                        content='\n'.join(current_block['content']).strip(),
                        indent_level=current_block['indent']
                    ))
                    block_id_counter += 1
                    
                # Start or continue quote block
                if current_block['type'] != 'quote':
                    current_block = {'type': 'quote', 'content': [quote_match.group(1)], 'indent': 0}
                else:
                    current_block['content'].append(quote_match.group(1))
                continue
                
            # Check for horizontal rules
            if re.match(r'^(---|\*\*\*|___)\s*$', line):
                # Finish the current block if any
                if current_block['content']:
                    blocks.append(Block(
                        id=f"{file_path.stem}_{block_id_counter}",
                        type=current_block['type'],
                        content='\n'.join(current_block['content']).strip(),
                        indent_level=current_block['indent']
                    ))
                    block_id_counter += 1
                
                # Add divider block
                blocks.append(Block(
                    id=f"{file_path.stem}_{block_id_counter}",
                    type='divider',
                    content='',
                    indent_level=0
                ))
                block_id_counter += 1
                current_block = {'type': 'paragraph', 'content': [], 'indent': 0}
                continue
                
            # Default case: add to current block
            current_block['content'].append(line)
            
        # Add the final block if there is one
        if current_block['content']:
            blocks.append(Block(
                id=f"{file_path.stem}_{block_id_counter}",
                type=current_block['type'],
                content='\n'.join(current_block['content']).strip(),
                indent_level=current_block['indent']
            ))
        
        return blocks
    
    def _parse_text(self, content: str, file_path: Path) -> List[Block]:
        """
        Parse plain text content into blocks.
        
        Args:
            content: The text content to parse
            file_path: Path to the source file (for block IDs)
            
        Returns:
            List[Block]: List of parsed blocks
        """
        blocks = []
        paragraphs = re.split(r'\n\s*\n', content)
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                blocks.append(Block(
                    id=f"{file_path.stem}_{i+1}",
                    type='paragraph',
                    content=paragraph.strip(),
                    indent_level=0
                ))
        
        return blocks
    
    def _get_combined_content(self, use_cache: bool = None) -> Tuple[Document, List[Block]]:
        """
        Get content for all files combined into a single document tree.
        
        Args:
            use_cache: Whether to use cache for this request
            
        Returns:
            Tuple[Document, List[Block]]: Document metadata and combined blocks
        """
        should_use_cache = self.cache_enabled if use_cache is None else use_cache
        
        # Check cache first if enabled
        if should_use_cache and hasattr(self, "cache_manager"):
            cached_doc, cached_blocks = self.cache_manager.get_cached_document("_combined_doctree")
            if cached_doc and cached_blocks:
                logger.debug("Using cached combined document")
                return cached_doc, cached_blocks
                
        # Get metadata for the combined document
        stats = self.directory_path.stat()
        created_time = datetime.fromtimestamp(stats.st_ctime)
        
        # Find all matching files
        files = list(self.directory_path.glob(self._get_file_pattern()))
        
        # Find the most recent modification time among all files
        most_recent_time = created_time
        for file in files:
            modified_time = datetime.fromtimestamp(file.stat().st_mtime)
            if modified_time > most_recent_time:
                most_recent_time = modified_time
        
        # Create document metadata
        doc = Document(
            id="_combined_doctree",
            title=self.directory_path.name,
            created_time=created_time,
            last_edited_time=most_recent_time,
            last_fetched=datetime.now(),
            source_id=f"local-{self.directory_path.name}"
        )
        
        # Start with a root heading for the directory
        all_blocks = [
            Block(
                id=f"root_heading",
                type="heading_1",
                content=self.directory_path.name,
                indent_level=0
            )
        ]
        
        # Sort files to process subdirectories in order
        sorted_files = sorted(files, key=lambda f: str(f.relative_to(self.directory_path)))
        
        # Track current directory structure to create hierarchical headings
        current_path_parts = []
        
        # Process each file
        for file in tqdm(sorted_files, desc="Building combined document tree", unit="file"):
            relative_path = file.relative_to(self.directory_path)
            path_parts = list(relative_path.parts)[:-1]  # Exclude the filename
            
            # Check if we've moved to a new directory in the hierarchy
            common_prefix_len = 0
            for i, (current, new) in enumerate(zip(current_path_parts, path_parts)):
                if current == new:
                    common_prefix_len = i + 1
                else:
                    break
            
            # Add directory headings for new directories in the path
            if len(path_parts) > common_prefix_len:
                for i, dir_name in enumerate(path_parts[common_prefix_len:]):
                    heading_level = min(2 + common_prefix_len + i, 6)  # Limit to h6
                    all_blocks.append(Block(
                        id=f"dir_{'_'.join(path_parts[:common_prefix_len+i+1])}",
                        type=f"heading_{heading_level}",
                        content=dir_name,
                        indent_level=0
                    ))
            
            # Update current path
            current_path_parts = path_parts
            
            # Add file heading
            all_blocks.append(Block(
                id=f"file_{str(relative_path).replace('/', '_')}",
                type="heading_2" if not path_parts else f"heading_{min(len(path_parts) + 3, 6)}",
                content=file.stem,
                indent_level=0
            ))
            
            # Parse file content and add its blocks
            try:
                file_blocks = self._parse_file_to_blocks(file)
                
                # Adjust block indent levels to fit the hierarchy
                base_indent = 1  # Start with indent 1 for file content
                for block in file_blocks:
                    block.indent_level += base_indent
                    all_blocks.append(block)
            except Exception as e:
                logger.error(f"Error parsing file {file}: {str(e)}")
                # Add error block
                all_blocks.append(Block(
                    id=f"error_{str(relative_path).replace('/', '_')}",
                    type="paragraph",
                    content=f"Error parsing file: {str(e)}",
                    indent_level=base_indent
                ))
        
        # Cache the combined document if enabled
        if should_use_cache and hasattr(self, "cache_manager"):
            self.cache_manager.cache_document("_combined_doctree", doc, all_blocks)
        
        return doc, all_blocks
