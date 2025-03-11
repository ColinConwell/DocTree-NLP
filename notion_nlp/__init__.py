"""
Notion NLP Library - Process Notion documents with NLP capabilities and hierarchical organization.
"""

from .notion_client import NotionClient
from .models import Document, Block, Tag
from .hierarchy import Hierarchy
from .tagger import Tagger
from .text_processor import TextProcessor
from .exceptions import NotionNLPError, AuthenticationError
from .env_loader import EnvLoader, get_env, get_required_env, get_api_key

__version__ = "0.1.0"

__all__ = [
    "NotionClient",
    "TextProcessor",
    "Hierarchy",
    "Tagger",
    "Document",
    "Block",
    "Tag",
    "NotionNLPError",
    "AuthenticationError",
    "EnvLoader",
    "get_env",
    "get_required_env",
    "get_api_key",
]
