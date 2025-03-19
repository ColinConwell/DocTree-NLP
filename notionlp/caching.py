"""
Cache management for Notion API responses.

This module handles caching of Notion API responses to reduce API calls
and manage rate limiting.
"""

import json
import time
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from tqdm.auto import tqdm

from .structure import Document, Block

# Set up logging
logger = logging.getLogger(__name__)

# Import defaults
from .defaults import get_default

# Constants from defaults for backward compatibility
DEFAULT_CACHE_DIR = get_default('cache.directory')
CACHE_SOURCE_NOTION = get_default('cache.sources.notion')
CACHE_SOURCE_INTERNAL = get_default('cache.sources.internal')
DEFAULT_CACHE_SOURCE = get_default('cache.default_source')

# Cache Manager ----------------------------------------------------------------


class CacheManager:
    """Manage caching of Notion API responses."""

    def __init__(
        self,
        api_token: str,
        cache_dir: str = DEFAULT_CACHE_DIR,
        max_age_days: Optional[int] = None,
        cache_source: str = DEFAULT_CACHE_SOURCE,
    ):
        """
        Initialize the cache manager.

        Args:
            api_token: Notion API token (used to segregate caches by API key)
            cache_dir: Directory to store cache files
            max_age_days: Maximum age of cache entries in days (None for no expiry)
            cache_source: Source of the cached documents (notion, internal, etc.)
        """
        # Create a token hash to use in the cache path to separate caches by API key
        token_hash = hashlib.md5(api_token.encode()).hexdigest()[:8]
        self.cache_dir = Path(cache_dir) / cache_source / token_hash
        self.max_age_seconds = max_age_days * 24 * 60 * 60 if max_age_days else None
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True)
            logger.info(f"Created cache directory: {self.cache_dir}")

    def _get_document_cache_path(self, doc_id: str) -> Path:
        """Get cache file path for a document."""
        return self.cache_dir / f"{doc_id}.json"

    def _get_document_list_cache_path(self) -> Path:
        """Get cache file path for the document list."""
        return self.cache_dir / "documents.json"

    def is_document_cached(
        self, doc_id: str, last_edited_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if document is cached and up to date.

        Args:
            doc_id: Document ID
            last_edited_time: Last edit time from Notion API

        Returns:
            bool: True if document is cached and up to date
        """
        cache_path = self._get_document_cache_path(doc_id)

        if not cache_path.exists():
            logger.debug(f"Document {doc_id} not found in cache")
            return False

        try:
            # If max_age is set, check file modification time for expiration
            if self.max_age_seconds is not None:
                mod_time = cache_path.stat().st_mtime
                if time.time() - mod_time > self.max_age_seconds:
                    logger.debug(f"Cache for document {doc_id} has expired")
                    return False

            # The primary check is comparing last_edited_time from API with cached version
            if last_edited_time:
                with open(cache_path, "r") as f:
                    cache_data = json.load(f)

                cached_time_str = cache_data.get("metadata", {}).get(
                    "last_edited_time", ""
                )
                if not cached_time_str:
                    logger.debug(f"No last_edited_time in cache for document {doc_id}")
                    return False

                cached_time = datetime.fromisoformat(cached_time_str)
                if cached_time < last_edited_time:
                    logger.debug(f"Document {doc_id} has been edited since last cached")
                    return False

                logger.debug(f"Using cached version of document {doc_id}")
                return True

            # If we don't have last_edited_time to compare, we assume cache is valid
            # unless max_age check failed above
            return True

        except Exception as e:
            logger.error(f"Error checking cache for document {doc_id}: {str(e)}")
            return False

    def is_document_list_cached(self) -> bool:
        """
        Check if document list is cached and not expired.

        Returns:
            bool: True if document list is cached and not expired
        """
        cache_path = self._get_document_list_cache_path()

        if not cache_path.exists():
            logger.debug("Document list not found in cache")
            return False

        try:
            # If max_age is set, check file modification time for expiration
            if self.max_age_seconds is not None:
                mod_time = cache_path.stat().st_mtime
                if time.time() - mod_time > self.max_age_seconds:
                    logger.debug("Document list cache has expired")
                    return False

            # Document list cache is considered valid if it exists and hasn't expired
            logger.debug("Using cached document list")
            return True

        except Exception as e:
            logger.error(f"Error checking cache for document list: {str(e)}")
            return False

    def cache_document(self, doc_id: str, document: Document, blocks: List[Block]):
        """
        Cache document content.

        Args:
            doc_id: Document ID
            document: Document metadata
            blocks: Document blocks
        """
        try:
            cache_path = self._get_document_cache_path(doc_id)

            cache_data = {
                "metadata": {
                    "id": document.id,
                    "title": document.title,
                    "created_time": document.created_time.isoformat(),
                    "last_edited_time": document.last_edited_time.isoformat(),
                    "last_fetched": datetime.now().isoformat(),
                },
                "blocks": [
                    {
                        "id": block.id,
                        "type": block.type,
                        "content": block.content,
                        "has_children": block.has_children,
                        "indent_level": block.indent_level,
                    }
                    for block in blocks
                ],
            }

            with open(cache_path, "w") as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(f"Cached document {doc_id}")

        except Exception as e:
            logger.error(f"Error caching document {doc_id}: {str(e)}")

    def cache_document_list(self, documents: List[Document]):
        """
        Cache document list.

        Args:
            documents: List of documents
        """
        try:
            cache_path = self._get_document_list_cache_path()

            # Process document data with progress bar
            doc_data = []
            for doc in tqdm(
                documents, desc="Preparing document list cache", unit="doc"
            ):
                doc_data.append(
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "created_time": doc.created_time.isoformat(),
                        "last_edited_time": doc.last_edited_time.isoformat(),
                    }
                )

            cache_data = {
                "metadata": {"last_fetched": datetime.now().isoformat()},
                "documents": doc_data,
            }

            with open(cache_path, "w") as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(f"Cached document list with {len(documents)} documents")

        except Exception as e:
            logger.error(f"Error caching document list: {str(e)}")

    def get_cached_document(
        self, doc_id: str
    ) -> tuple[Optional[Document], Optional[List[Block]]]:
        """
        Get cached document content.

        Args:
            doc_id: Document ID

        Returns:
            tuple: (Document metadata, list of blocks) or (None, None) if not cached
        """
        cache_path = self._get_document_cache_path(doc_id)

        if not cache_path.exists():
            return None, None

        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            metadata = cache_data.get("metadata", {})
            blocks_data = cache_data.get("blocks", [])

            document = Document(
                id=metadata.get("id", ""),
                title=metadata.get("title", ""),
                created_time=datetime.fromisoformat(metadata.get("created_time", "")),
                last_edited_time=datetime.fromisoformat(
                    metadata.get("last_edited_time", "")
                ),
                last_fetched=datetime.fromisoformat(metadata.get("last_fetched", "")),
            )

            blocks = [
                Block(
                    id=block.get("id", ""),
                    type=block.get("type", ""),
                    content=block.get("content", ""),
                    has_children=block.get("has_children", False),
                    indent_level=block.get("indent_level", 0),
                )
                for block in blocks_data
            ]

            return document, blocks

        except Exception as e:
            logger.error(f"Error reading cache for document {doc_id}: {str(e)}")
            return None, None

    def get_cached_document_list(self) -> Optional[List[Document]]:
        """
        Get cached document list.

        Returns:
            List[Document]: List of documents or None if not cached
        """
        cache_path = self._get_document_list_cache_path()

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            docs_data = cache_data.get("documents", [])

            documents = [
                Document(
                    id=doc.get("id", ""),
                    title=doc.get("title", ""),
                    created_time=datetime.fromisoformat(doc.get("created_time", "")),
                    last_edited_time=datetime.fromisoformat(
                        doc.get("last_edited_time", "")
                    ),
                )
                for doc in docs_data
            ]

            return documents

        except Exception as e:
            logger.error(f"Error reading cache for document list: {str(e)}")
            return None

    def clear_cache(self):
        """Clear all cache files."""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            for cache_file in tqdm(cache_files, desc="Clearing cache", unit="file"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")

    def clear_document_cache(self, doc_id: str):
        """
        Clear cache for a specific document.

        Args:
            doc_id: Document ID
        """
        try:
            cache_path = self._get_document_cache_path(doc_id)
            if cache_path.exists():
                cache_path.unlink()
                logger.debug(f"Cleared cache for document {doc_id}")

            # Also clear any raw data cache for this document
            raw_cache_path = self.cache_dir / f"{doc_id}_raw.json"
            if raw_cache_path.exists():
                raw_cache_path.unlink()
                logger.debug(f"Cleared raw data cache for document {doc_id}")
        except Exception as e:
            logger.error(f"Error clearing cache for document {doc_id}: {str(e)}")

    def get_cached_data(self, cache_key: str) -> Optional[dict]:
        """
        Get cached raw data by key.

        Args:
            cache_key: Cache key (usually document_id with a suffix)

        Returns:
            Optional[dict]: Cached data or None if not found
        """
        cache_path = self.cache_dir / f"{cache_key}.json"

        if not cache_path.exists():
            return None

        try:
            # If max_age is set, check file modification time for expiration
            if self.max_age_seconds is not None:
                mod_time = cache_path.stat().st_mtime
                if time.time() - mod_time > self.max_age_seconds:
                    logger.debug(f"Cache for {cache_key} has expired")
                    return None

            with open(cache_path, "r") as f:
                cache_data = json.load(f)

            return cache_data

        except Exception as e:
            logger.error(f"Error reading cache for {cache_key}: {str(e)}")
            return None

    def cache_raw_data(self, cache_key: str, data: dict):
        """
        Cache raw data.

        Args:
            cache_key: Cache key (usually document_id with a suffix)
            data: Data to cache
        """
        try:
            cache_path = self.cache_dir / f"{cache_key}.json"

            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Cached raw data for {cache_key}")

        except Exception as e:
            logger.error(f"Error caching raw data for {cache_key}: {str(e)}")


# Helper Functions ------------------------------------------------------------


def get_cache_dir(cache_source: str = DEFAULT_CACHE_SOURCE) -> Path:
    """
    Get the default cache directory.
    
    Args:
        cache_source: Source of the cached documents (notion, internal, etc.)
    """
    return Path(DEFAULT_CACHE_DIR) / cache_source


def get_api_specific_cache_dir(api_token: str, cache_source: str = DEFAULT_CACHE_SOURCE) -> Path:
    """
    Get the API-specific cache directory.
    
    Args:
        api_token: API token for API-specific cache
        cache_source: Source of the cached documents (notion, internal, etc.)
    """
    token_hash = hashlib.md5(api_token.encode()).hexdigest()[:8]
    return get_cache_dir(cache_source) / token_hash


def get_cache_path(doc_id: str, api_token: Optional[str] = None, cache_source: str = DEFAULT_CACHE_SOURCE) -> Path:
    """
    Get the cache path for a document.

    Args:
        doc_id: Document ID
        api_token: Optional API token for API-specific cache
        cache_source: Source of the cached documents (notion, internal, etc.)

    Returns:
        Path: Cache file path
    """
    if api_token:
        return get_api_specific_cache_dir(api_token, cache_source) / f"{doc_id}.json"
    else:
        return get_cache_dir(cache_source) / f"{doc_id}.json"
