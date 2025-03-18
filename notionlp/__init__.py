"""
Notion NLP Library - Process Notion documents with NLP capabilities and hierarchical organization.
"""

__version__ = "0.1.0"

from .api_client import (
    NotionClient, NotionNLPError, AuthenticationError, CacheError
)

from .env_loader import (
    EnvLoader, get_env, get_required_env, get_api_key, find_notion_token
)

from .structure import (
    Document, Block, Tag, Hierarchy, Tagger
)

from .parsers import (
    doc_to_dict, export_to_markdown, export_to_rst, load_example_document
)

from .text_processor import TextProcessor

from .cache_manager import (
    CacheManager, DEFAULT_CACHE_DIR
)

from .rate_limiter import RateLimiter

DATA_STRUCTURES = [
    "Document",
    "Block",
    "Tag",
    "Hierarchy",
    "Tagger"
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

__all__ = [
    # Core components
    "NotionClient",
    "RateLimiter",
    
    # Helper modules
    "EnvLoader",
    *DATA_STRUCTURES,
    *ENV_HELPERS,
    *CACHE_CONFIG,
    
    # Processing
    "TextProcessor",
    "doc_to_dict",
    "export_to_markdown",
    "export_to_rst",
    "load_example_document",
    
    # Errors
    *ERRORS,
]