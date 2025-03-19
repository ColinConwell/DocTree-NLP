"""
DocTree NLP: A toolkit for processing document trees with NLP capabilities.

This package provides tools for retrieving, caching, parsing, and analyzing
content from various document sources including Notion, Obsidian, and local files.
"""

__version__ = "0.5.0"

from .api_client import (
    NotionClient, ObsidianClient, LocalSource, 
    DocTreeError, AuthenticationError, CacheError
)

from .env_loader import (
    EnvLoader, get_env, get_required_env, get_api_key, find_notion_token
)

from .structure import (
    Document, Block, Tag, Hierarchy, Tagger, DocTree, Source, Node
)

from .text_processor import TextProcessor

from .caching import (
    CacheManager, DEFAULT_CACHE_DIR, CACHE_SOURCE_NOTION, CACHE_SOURCE_INTERNAL
)

from .defaults import (
    get_defaults, get_default, set_default, update_defaults,
    load_defaults_from_env, load_defaults_from_file, save_defaults_to_file
)

from .rate_limiter import RateLimiter

# Performance optimization components
from .lazy_document import (
    LazyDocument, LazyDocumentCollection, create_lazy_document
)

from .windowing import (
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
    "DEFAULT_CACHE_DIR",
    "CACHE_SOURCE_NOTION", 
    "CACHE_SOURCE_INTERNAL"
]

DEFAULTS_CONFIG = [
    "get_defaults",
    "get_default",
    "set_default",
    "update_defaults",
    "load_defaults_from_env",
    "load_defaults_from_file",
    "save_defaults_to_file"
]

ERRORS = [
    "DocTreeError",    # Base error class 
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

SOURCES = [
    "NotionClient",
    "ObsidianClient",
    "LocalSource"
]

__all__ = [
    # Data sources
    *SOURCES,
    "RateLimiter",
    
    # Helper modules
    "EnvLoader",
    *DATA_STRUCTURES,
    *ENV_HELPERS,
    *CACHE_CONFIG,
    *DEFAULTS_CONFIG,
    *NOTEBOOK_HELPERS,
    
    # Processing
    "TextProcessor",
    
    # Performance optimization components
    *PERFORMANCE_TOOLS,
    
    # Errors
    *ERRORS,
]