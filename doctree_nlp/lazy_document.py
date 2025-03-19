"""
Lazy loading implementation for Document objects.

This module provides LazyDocument class that implements lazy loading for documents,
allowing efficient handling of large document collections by only loading content
when needed.
"""

import logging
from typing import List, Dict, Any, Optional, Callable, Union
from functools import wraps
from datetime import datetime
from pathlib import Path

from .structure import Document, Block, DocTree
from .api_client import NotionClient

logger = logging.getLogger(__name__)

class LazyDocument(Document):
    """
    Document implementation with lazy loading capabilities.
    
    This class extends Document to provide lazy loading of blocks and tree structure,
    which is particularly useful for large documents.
    """
    
    def __init__(
        self,
        id: str,
        title: str,
        created_time: datetime,
        last_edited_time: datetime,
        source_id: Optional[str] = None,
        client: Optional[NotionClient] = None,
        load_strategy: str = "on_demand",
        **kwargs
    ):
        """
        Initialize a lazy document.
        
        Args:
            id: Document ID
            title: Document title
            created_time: Creation timestamp
            last_edited_time: Last edit timestamp
            source_id: Optional source identifier
            client: NotionClient instance for loading content
            load_strategy: Strategy for loading content ('on_demand', 'async', 'preload')
            **kwargs: Additional arguments passed to Document
        """
        # Initialize with default empty blocks
        blocks = kwargs.pop('blocks', []) if 'blocks' in kwargs else []
        
        super().__init__(
            id=id,
            title=title,
            created_time=created_time,
            last_edited_time=last_edited_time,
            source_id=source_id,
            blocks=blocks,
            **kwargs
        )
        
        self._client = client
        self._load_strategy = load_strategy
        self._blocks_loaded = len(blocks) > 0
        self._tree_loaded = self.tree is not None
        self._loading_in_progress = False
        
    def _load_blocks_if_needed(self):
        """Ensure blocks are loaded before accessing them."""
        if not self._blocks_loaded and not self._loading_in_progress:
            self._loading_in_progress = True
            try:
                if self._client:
                    logger.debug(f"Lazy loading blocks for document {self.id}")
                    try:
                        document, blocks = self._client.get_document_content(self.id)
                        if blocks:
                            # Use internal method to set blocks directly
                            super().__setattr__('blocks', blocks)
                            super().__setattr__('_blocks_loaded', True)
                        else:
                            logger.warning(f"Failed to load blocks for document {self.id}")
                    except Exception as e:
                        logger.error(f"Error loading blocks for document {self.id}: {str(e)}")
                        # Keep empty blocks but mark as loaded to prevent repeated attempts
                        super().__setattr__('_blocks_loaded', True)
                else:
                    logger.warning(f"No client available to load blocks for document {self.id}")
            finally:
                self._loading_in_progress = False
    
    def _ensure_tree_built(self):
        """Ensure tree is built before accessing it."""
        self._load_blocks_if_needed()
        
        if not self._tree_loaded and not self._loading_in_progress:
            self._loading_in_progress = True
            try:
                if self.blocks:
                    logger.debug(f"Building tree for document {self.id}")
                    self.tree = super().build_tree()
                    self._tree_loaded = True
                else:
                    logger.warning(f"No blocks available to build tree for document {self.id}")
            finally:
                self._loading_in_progress = False
    
    # Override methods that need to ensure blocks are loaded
    
    # Use __getattribute__ for lazy loading of blocks
    def __getattribute__(self, name):
        """Custom attribute access with lazy loading."""
        # For special attributes, bypass lazy loading logic
        if name.startswith('_') or name == '__dict__':
            return super().__getattribute__(name)
            
        # If accessing blocks, ensure they're loaded
        if name == 'blocks':
            # Get _blocks_loaded flag without recursion
            blocks_loaded = super().__getattribute__('_blocks_loaded')
            loading_in_progress = super().__getattribute__('_loading_in_progress')
            
            # If blocks not loaded and not already loading, trigger loading
            if not blocks_loaded and not loading_in_progress:
                # Call the loading method directly to avoid recursion
                load_method = super().__getattribute__('_load_blocks_if_needed')
                load_method()
        
        # Get the actual attribute
        return super().__getattribute__(name)
        
    def __setattr__(self, name, value):
        """Custom attribute setting with special handling for blocks."""
        if name == 'blocks':
            # First set blocks using parent's __setattr__
            super().__setattr__(name, value)
            # Then mark as loaded
            super().__setattr__('_blocks_loaded', True)
        else:
            # Use normal setattr for other attributes
            super().__setattr__(name, value)
    
    def build_tree(self) -> DocTree:
        """Build document tree with lazy loading."""
        self._load_blocks_if_needed()
        result = super().build_tree()
        self._tree_loaded = True
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary with lazy loading."""
        self._ensure_tree_built()
        return super().to_dict()
    
    def to_markdown(self) -> str:
        """Convert document to Markdown with lazy loading."""
        self._ensure_tree_built()
        return super().to_markdown()
    
    def to_rst(self) -> str:
        """Convert document to RST with lazy loading."""
        self._ensure_tree_built()
        return super().to_rst()
    
    def preview_blocks(self, n: int = 5) -> List[Block]:
        """Show block preview with lazy loading."""
        self._load_blocks_if_needed()
        return super().preview_blocks(n)
    
    def preview_text(self, n_chars: int = 500) -> str:
        """Show text preview with lazy loading."""
        self._load_blocks_if_needed()
        return super().preview_text(n_chars)
    
    def preview_sentences(self, n: int = 3) -> str:
        """Show sentence preview with lazy loading."""
        self._load_blocks_if_needed()
        return super().preview_sentences(n)


class LazyDocumentCollection:
    """
    Collection of lazy-loaded documents.
    
    This class manages a collection of LazyDocument objects, providing
    batch operations and efficient memory usage.
    """
    
    def __init__(
        self,
        client: NotionClient,
        preload_metadata: bool = True,
        load_strategy: str = "on_demand"
    ):
        """
        Initialize the lazy document collection.
        
        Args:
            client: NotionClient instance for loading documents
            preload_metadata: Whether to preload document metadata
            load_strategy: Default strategy for loading document content
        """
        self.client = client
        self.documents: Dict[str, LazyDocument] = {}
        self.load_strategy = load_strategy
        
        if preload_metadata:
            self._preload_document_metadata()
    
    def _preload_document_metadata(self):
        """Preload metadata for all available documents."""
        logger.info("Preloading document metadata")
        document_list = self.client.list_documents()
        
        for doc in document_list:
            lazy_doc = LazyDocument(
                id=doc.id,
                title=doc.title,
                created_time=doc.created_time,
                last_edited_time=doc.last_edited_time,
                client=self.client,
                load_strategy=self.load_strategy
            )
            self.documents[doc.id] = lazy_doc
        
        logger.info(f"Preloaded metadata for {len(self.documents)} documents")
    
    def get_document(self, doc_id: str) -> Optional[LazyDocument]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            LazyDocument: The document if found, None otherwise
        """
        if doc_id in self.documents:
            return self.documents[doc_id]
        
        # Try to load the document if not in collection
        try:
            document, blocks = self.client.get_document_content(doc_id)
            if document:
                lazy_doc = LazyDocument(
                    id=document.id,
                    title=document.title,
                    created_time=document.created_time,
                    last_edited_time=document.last_edited_time,
                    client=self.client,
                    load_strategy=self.load_strategy
                )
                # If blocks were already fetched, add them
                if blocks:
                    lazy_doc.blocks = blocks
                
                self.documents[doc_id] = lazy_doc
                return lazy_doc
        except Exception as e:
            logger.error(f"Error loading document {doc_id}: {str(e)}")
        
        return None
    
    def search_documents(
        self, 
        query: str, 
        search_titles: bool = True,
        search_content: bool = False
    ) -> List[LazyDocument]:
        """
        Search documents by title or content.
        
        Args:
            query: Search query
            search_titles: Whether to search document titles
            search_content: Whether to search document content (may trigger loading)
            
        Returns:
            List[LazyDocument]: Matching documents
        """
        results = []
        query = query.lower()
        
        for doc_id, document in self.documents.items():
            # Search titles
            if search_titles and query in document.title.lower():
                results.append(document)
                continue
            
            # Search content if requested (this may trigger loading)
            if search_content:
                # Only load blocks for this search, not tree
                if not document._blocks_loaded:
                    document._load_blocks_if_needed()
                
                # Search in block content
                for block in document.blocks:
                    if query in block.content.lower():
                        results.append(document)
                        break
        
        return results
    
    def batch_preload(self, doc_ids: List[str]):
        """
        Preload multiple documents in batch.
        
        Args:
            doc_ids: List of document IDs to preload
        """
        for doc_id in doc_ids:
            if doc_id in self.documents:
                self.documents[doc_id]._load_blocks_if_needed()
    
    def clear_loaded_content(self, keep_metadata: bool = True):
        """
        Clear loaded content to free memory.
        
        Args:
            keep_metadata: Whether to keep document metadata
        """
        if keep_metadata:
            # Keep documents but clear their content
            for doc_id, document in self.documents.items():
                # Reset blocks with empty list
                super(LazyDocument, document).__setattr__('blocks', [])
                # Reset tree to None
                super(LazyDocument, document).__setattr__('tree', None)
                # Reset flags
                super(LazyDocument, document).__setattr__('_blocks_loaded', False)
                super(LazyDocument, document).__setattr__('_tree_loaded', False)
        else:
            # Clear all documents
            self.documents.clear()


# Factory function to create LazyDocument instances
def create_lazy_document(
    doc_id: str,
    client: NotionClient,
    load_strategy: str = "on_demand"
) -> LazyDocument:
    """
    Create a lazy document with the given ID.
    
    Args:
        doc_id: Document ID
        client: NotionClient instance
        load_strategy: Strategy for loading content
        
    Returns:
        LazyDocument: The created lazy document
    """
    # First get metadata
    document = client._get_document_metadata(doc_id)
    
    if document:
        return LazyDocument(
            id=document.id,
            title=document.title,
            created_time=document.created_time,
            last_edited_time=document.last_edited_time,
            last_fetched=document.last_fetched,
            client=client,
            load_strategy=load_strategy
        )
    
    return None