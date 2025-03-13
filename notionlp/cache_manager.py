"""
Cache management for Notion API responses.

This module handles caching of Notion API responses to reduce API calls
and manage rate limiting.
"""
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from .structure import Document, Block

# Set up logging
logger = logging.getLogger(__name__)

# Default cache location
DEFAULT_CACHE_DIR = "notion_cache"

class CacheManager:
    """Manage caching of Notion API responses."""

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR, max_age_days: int = 1):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files
            max_age_days: Maximum age of cache entries in days
        """
        self.cache_dir = Path(cache_dir)
        self.max_age_seconds = max_age_days * 24 * 60 * 60
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

    def is_document_cached(self, doc_id: str, last_edited_time: Optional[datetime] = None) -> bool:
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
            return False
            
        try:
            # Check file modification time first for quick rejection
            mod_time = cache_path.stat().st_mtime
            if time.time() - mod_time > self.max_age_seconds:
                return False
                
            # If we have a last_edited_time, check that too
            if last_edited_time:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                
                cached_time = datetime.fromisoformat(cache_data.get('metadata', {}).get('last_edited_time', ''))
                if cached_time < last_edited_time:
                    return False
                    
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
            return False
            
        try:
            # Check file modification time
            mod_time = cache_path.stat().st_mtime
            if time.time() - mod_time > self.max_age_seconds:
                return False
                
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
                'metadata': {
                    'id': document.id,
                    'title': document.title,
                    'created_time': document.created_time.isoformat(),
                    'last_edited_time': document.last_edited_time.isoformat(),
                    'last_fetched': datetime.now().isoformat()
                },
                'blocks': [
                    {
                        'id': block.id,
                        'type': block.type,
                        'content': block.content,
                        'has_children': block.has_children,
                        'indent_level': block.indent_level
                    }
                    for block in blocks
                ]
            }
            
            with open(cache_path, 'w') as f:
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
            
            cache_data = {
                'metadata': {
                    'last_fetched': datetime.now().isoformat()
                },
                'documents': [
                    {
                        'id': doc.id,
                        'title': doc.title,
                        'created_time': doc.created_time.isoformat(),
                        'last_edited_time': doc.last_edited_time.isoformat()
                    }
                    for doc in documents
                ]
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Cached document list with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error caching document list: {str(e)}")

    def get_cached_document(self, doc_id: str) -> tuple[Optional[Document], Optional[List[Block]]]:
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
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                
            metadata = cache_data.get('metadata', {})
            blocks_data = cache_data.get('blocks', [])
            
            document = Document(
                id=metadata.get('id', ''),
                title=metadata.get('title', ''),
                created_time=datetime.fromisoformat(metadata.get('created_time', '')),
                last_edited_time=datetime.fromisoformat(metadata.get('last_edited_time', '')),
                last_fetched=datetime.fromisoformat(metadata.get('last_fetched', ''))
            )
            
            blocks = [
                Block(
                    id=block.get('id', ''),
                    type=block.get('type', ''),
                    content=block.get('content', ''),
                    has_children=block.get('has_children', False),
                    indent_level=block.get('indent_level', 0)
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
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                
            docs_data = cache_data.get('documents', [])
            
            documents = [
                Document(
                    id=doc.get('id', ''),
                    title=doc.get('title', ''),
                    created_time=datetime.fromisoformat(doc.get('created_time', '')),
                    last_edited_time=datetime.fromisoformat(doc.get('last_edited_time', ''))
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
            for cache_file in self.cache_dir.glob('*.json'):
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
        except Exception as e:
            logger.error(f"Error clearing cache for document {doc_id}: {str(e)}")