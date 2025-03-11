"""
Notion NLP Library - Process Notion documents with NLP capabilities and hierarchical organization.
"""

from .client import NotionClient
from .core import Document, Block, Tag, Hierarchy, Tagger, NotionNLPError, AuthenticationError
from .text_processor import TextProcessor
from .parsers import (
    EnvLoader, get_env, get_required_env, get_api_key,
    doc_to_dict, export_to_markdown, export_to_rst, load_example_document
)

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
    "doc_to_dict",
    "export_to_markdown",
    "export_to_rst",
    "load_example_document",
]