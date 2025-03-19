"""
Notion API client implementation with enhanced content handling.
"""

import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union, Literal
from tqdm.auto import tqdm

from .structure import Document, Block
from .cache_manager import CacheManager, DEFAULT_CACHE_DIR
from .rate_limiter import RateLimiter
from .env_loader import find_notion_token

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Notion Client ----------------------------------------------------------------


class NotionClient:
    """Client for interacting with Notion API with enhanced content handling."""

    BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"
    DEFAULT_RATE_LIMIT = 3  # API limit: 3 requests per second
    DEFAULT_CACHE_ENABLED = True
    DEFAULT_MAX_CACHE_AGE_DAYS = None  # No expiration by default
    AUTO_TOKEN = "auto"  # Special value to auto-discover token

    def __init__(
        self,
        token: Union[str, Literal["auto"]] = AUTO_TOKEN,
        cache_enabled: bool = DEFAULT_CACHE_ENABLED,
        cache_dir: str = DEFAULT_CACHE_DIR,
        max_cache_age_days: Optional[int] = DEFAULT_MAX_CACHE_AGE_DAYS,
        rate_limit: int = DEFAULT_RATE_LIMIT,
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
        if token == self.AUTO_TOKEN:
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
            "Notion-Version": self.API_VERSION,
            "Content-Type": "application/json",
        }

        # Initialize cache manager if enabled
        self.cache_enabled = cache_enabled
        if self.cache_enabled:
            self.cache_manager = CacheManager(
                api_token=token,  # Pass token to create API-specific cache
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


class AuthenticationError(NotionNLPError):
    """Raised when authentication fails."""

    pass


class CacheError(NotionNLPError):
    """Raised when cache operations fail."""

    pass
