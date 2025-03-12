"""
Notion NLP Library - Process Notion documents with NLP capabilities and hierarchical organization.
"""

__version__ = "0.1.0"

from .api_client import (
    NotionClient, NotionNLPError, AuthenticationError
)

from .api_env import (
    EnvLoader, get_env, get_required_env, get_api_key
)

from .structure import (
    Document, Block, Tag, Hierarchy, Tagger
)

from .parsers import (
    doc_to_dict, export_to_markdown, export_to_rst, load_example_document
)

from .text_processor import TextProcessor

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
]

__all__ = [
    "NotionClient",
    "EnvLoader",
    *DATA_STRUCTURES,
    *ENV_HELPERS,
    "TextProcessor",
    "doc_to_dict",
    "export_to_markdown",
    "export_to_rst",
    "load_example_document",
]