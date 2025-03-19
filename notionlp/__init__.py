"""
NotioNLPToolkit: A toolkit for natural language processing of Notion documents.

This package provides tools for retrieving, caching, parsing, and analyzing
content from Notion documents using the official Notion API.
"""

__version__ = "0.4.0"

from .api_client import (
    NotionClient, NotionNLPError, AuthenticationError, CacheError
)

from .env_loader import (
    EnvLoader, get_env, get_required_env, get_api_key, find_notion_token
)

from .structure import (
    Document, Block, Tag, Hierarchy, Tagger, DocTree, Source, Node
)

from .text_processor import TextProcessor

from .cache_manager import (
    CacheManager, DEFAULT_CACHE_DIR
)

from .rate_limiter import RateLimiter

# Performance optimization components
from .lazy_document import (
    LazyDocument, LazyDocumentCollection, create_lazy_document
)

from .document_windowing import (
    DocumentWindow, DocumentWindower, TreeWindower
)

# Optional Jupyter notebook support
try:
    from .notebook import (
        display_document, display_document_tree, display_document_table
    )
    NOTEBOOK_HELPERS = [
        "display_document", 
        "display_document_tree", 
        "display_document_table"
    ]
except ImportError:
    NOTEBOOK_HELPERS = []

DATA_STRUCTURES = [
    "Document",
    "Block",
    "Tag",
    "Node",
    "DocTree",
    "Hierarchy",  # For backward compatibility
    "Tagger",
    "Source"
]

ENV_HELPERS = [
    "EnvLoader",
    "get_env",
    "get_required_env",
    "get_api_key",
    "find_notion_token",
]

CACHE_CONFIG = [
    "CacheManager",
    "DEFAULT_CACHE_DIR"
]

ERRORS = [
    "NotionNLPError",
    "AuthenticationError",
    "CacheError"
]

PERFORMANCE_TOOLS = [
    "LazyDocument",
    "LazyDocumentCollection",
    "create_lazy_document",
    "DocumentWindow",
    "DocumentWindower",
    "TreeWindower"
]

__all__ = [
    # Core components
    "NotionClient",
    "RateLimiter",
    
    # Helper modules
    "EnvLoader",
    *DATA_STRUCTURES,
    *ENV_HELPERS,
    *CACHE_CONFIG,
    *NOTEBOOK_HELPERS,
    
    # Processing
    "TextProcessor",
    
    # Performance optimization components
    *PERFORMANCE_TOOLS,
    
    # Errors
    *ERRORS,
]