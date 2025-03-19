"""
DEPRECATED: API environment variable handling.

This module is deprecated. Please use env_loader instead.

It is maintained for backward compatibility but will be removed in a future version.
"""
import logging
import warnings
from typing import Optional, Any

from .env_loader import (
    EnvLoader as _EnvLoader,
    get_env as _get_env,
    get_required_env as _get_required_env,
    get_api_key as _get_api_key
)

# Set up logging
logger = logging.getLogger(__name__)

# Show deprecation warning
warnings.warn(
    "doctree_nlp.api_env is deprecated. Please use doctree_nlp.env_loader instead.",
    DeprecationWarning,
    stacklevel=2
)

# Environment Variable Loading ----------------------------------------------------

DOTENV_AVAILABLE = True  # Always true since we're using env_loader now

def _load_dotenv():
    """
    DEPRECATED: Load the .env file if it exists.
    
    This is kept for backwards compatibility but does nothing.
    """
    warnings.warn(
        "_load_dotenv is deprecated. env_loader automatically loads .env files.",
        DeprecationWarning,
        stacklevel=2
    )

class EnvLoader(_EnvLoader):
    """
    DEPRECATED: Handle environment variable loading from various sources.
    
    This class is kept for backwards compatibility but delegates to env_loader.EnvLoader.
    """
    
    def __init__(self, load_dotenv_file: bool = True, dotenv_path: Optional[str] = None):
        """
        DEPRECATED: Initialize the environment loader.
        
        Args:
            load_dotenv_file: Whether to attempt loading from .env file
            dotenv_path: Path to .env file (default: search in current directory)
        """
        warnings.warn(
            "api_env.EnvLoader is deprecated. Please use env_loader.EnvLoader instead.",
            DeprecationWarning,
            stacklevel=2
        )
        search_parent_dirs = dotenv_path is None
        max_search_depth = 0 if dotenv_path is not None else 2
        super().__init__(
            search_parent_dirs=search_parent_dirs,
            max_search_depth=max_search_depth,
            allow_interactive=False  # Keep old behavior for backward compatibility
        )

# Create a default instance for easy import
env = EnvLoader()

def get_env(key: str, default: Any = None) -> Any:
    """
    DEPRECATED: Get an environment variable using the default loader.
    
    Args:
        key: Environment variable key
        default: Default value if key not found
        
    Returns:
        Value of environment variable or default
    """
    warnings.warn(
        "api_env.get_env is deprecated. Please use env_loader.get_env instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return _get_env(key, default)

def get_required_env(key: str) -> str:
    """
    DEPRECATED: Get a required environment variable using the default loader.
    
    Args:
        key: Environment variable key
        
    Returns:
        Value of environment variable
        
    Raises:
        ValueError: If environment variable is not found
    """
    warnings.warn(
        "api_env.get_required_env is deprecated. Please use env_loader.get_required_env instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return _get_required_env(key)

def get_api_key(service: str) -> str:
    """
    DEPRECATED: Get an API key for a specific service using the default loader.
    
    Args:
        service: Service name (e.g., 'openai', 'anthropic')
        
    Returns:
        API key for the service
        
    Raises:
        ValueError: If API key is not found
    """
    warnings.warn(
        "api_env.get_api_key is deprecated. Please use env_loader.get_api_key instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return _get_api_key(service)