"""
Default configuration management for DocTree-NLP.

This module provides a centralized configuration system for managing default settings
across the toolkit, with support for loading from environment files or config files.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class DefaultsManager:
    """
    Manages default configuration settings for DocTree-NLP.
    
    This class provides a central configuration system with dictionary-like access,
    the ability to load settings from environment variables, JSON, or YAML files.
    """
    
    def __init__(self):
        """Initialize defaults manager with standard default values."""
        self._defaults = {
            # Cache settings
            "cache": {
                "directory": "cache",
                "sources": {
                    "internal": "internal",
                    "notion": "notion",
                    "obsidian": "obsidian",
                    "local": "local",
                },
                "default_source": "notion",
                "max_age_days": None,
                "enabled": True,
            },
            
            # API settings
            "api": {
                "version": "2022-06-28",
                "rate_limit": 3,
                "auto_token": "auto",
            },
            
            # Document settings
            "document": {
                "window_size": 50,
                "tree_nodes_per_window": 20,
            },
            
            # Obsidian settings
            "obsidian": {
                "parse_links": True,      # Parse [[wiki-links]]
                "parse_tags": True,       # Parse #tags
                "follow_embeds": True,    # Follow ![[embeds]]
                "follow_backlinks": False, # Include backlinks in document processing
            },
            
            # Local source settings
            "local": {
                "default_pattern": "**/*.md",  # Default glob pattern for files
                "recursive_search": True,     # Whether to search subdirectories
                "encoding": "utf-8",          # Default file encoding
            },
            
            # Logging
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            }
        }
    
    def __getitem__(self, key: str) -> Any:
        """Get a configuration value using dictionary access."""
        keys = key.split('.')
        value = self._defaults
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                raise KeyError(f"Configuration key not found: {key}")
        
        return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set a configuration value using dictionary access."""
        keys = key.split('.')
        target = self._defaults
        
        # Navigate to the right level
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            if not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]
        
        # Set the value
        target[keys[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value with an optional default.
        
        Args:
            key: Dot-notation key (e.g., 'cache.directory')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        try:
            return self[key]
        except KeyError:
            return default
    
    def update(self, config: Dict[str, Any]) -> None:
        """
        Update multiple configuration values at once.
        
        Args:
            config: Dictionary of configuration values
        """
        def _update_recursive(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    _update_recursive(target[key], value)
                else:
                    target[key] = value
        
        _update_recursive(self._defaults, config)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get a copy of the entire configuration as a dictionary.
        
        Returns:
            Dict: Configuration dictionary
        """
        import copy
        return copy.deepcopy(self._defaults)
    
    def load_env(self, env_file: Optional[str] = None, prefix: str = "DOCTREE_") -> None:
        """
        Load configuration from environment variables.
        
        Args:
            env_file: Path to .env file (optional)
            prefix: Prefix for environment variables to consider
        """
        # Load .env file if specified
        if env_file:
            if not os.path.exists(env_file):
                logger.warning(f"Env file not found: {env_file}")
                return
            load_dotenv(env_file)
        
        # Process all environment variables with the specified prefix
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase config keys
                config_key = key[len(prefix):].lower().replace('_', '.')
                
                # Try to convert to appropriate type
                if value.lower() in ("true", "yes", "1"):
                    value = True
                elif value.lower() in ("false", "no", "0"):
                    value = False
                elif value.lower() == "none":
                    value = None
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                    value = float(value)
                
                # Update config
                try:
                    self[config_key] = value
                    logger.debug(f"Loaded config from env: {config_key}={value}")
                except Exception as e:
                    logger.warning(f"Failed to set config from env {key}: {str(e)}")
    
    def load_file(self, file_path: Union[str, Path]) -> bool:
        """
        Load configuration from a JSON or YAML file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            bool: True if file was loaded successfully
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ('.yaml', '.yml'):
                    config = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    logger.warning(f"Unsupported config file format: {file_path}")
                    return False
            
            if not isinstance(config, dict):
                logger.warning(f"Invalid config file format: {file_path}")
                return False
                
            self.update(config)
            logger.info(f"Loaded configuration from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading config from {file_path}: {str(e)}")
            return False

    def save_file(self, file_path: Union[str, Path], format: str = 'json') -> bool:
        """
        Save current configuration to a file.
        
        Args:
            file_path: Path to save configuration file
            format: Format to save ('json' or 'yaml')
            
        Returns:
            bool: True if file was saved successfully
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'w') as f:
                if format.lower() == 'yaml':
                    yaml.dump(self._defaults, f, default_flow_style=False)
                else:
                    json.dump(self._defaults, f, indent=2)
            
            logger.info(f"Saved configuration to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config to {file_path}: {str(e)}")
            return False


# Create a singleton instance
_defaults_manager = DefaultsManager()

# Convenience functions
def get_defaults() -> DefaultsManager:
    """Get the defaults manager instance."""
    return _defaults_manager

def get_default(key: str, default: Any = None) -> Any:
    """
    Get a specific default value.
    
    Args:
        key: Dot-notation configuration key (e.g., 'cache.directory')
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    return _defaults_manager.get(key, default)

def set_default(key: str, value: Any) -> None:
    """
    Set a specific default value.
    
    Args:
        key: Dot-notation configuration key (e.g., 'cache.directory')
        value: Value to set
    """
    _defaults_manager[key] = value

def update_defaults(config: Dict[str, Any]) -> None:
    """
    Update multiple default values.
    
    Args:
        config: Dictionary of configuration values to update
    """
    _defaults_manager.update(config)

def load_defaults_from_env(env_file: Optional[str] = None) -> None:
    """
    Load defaults from environment variables.
    
    Args:
        env_file: Path to .env file (optional)
    """
    _defaults_manager.load_env(env_file)

def load_defaults_from_file(file_path: Union[str, Path]) -> bool:
    """
    Load defaults from a JSON or YAML file.
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        bool: True if file was loaded successfully
    """
    return _defaults_manager.load_file(file_path)

def save_defaults_to_file(file_path: Union[str, Path], format: str = 'json') -> bool:
    """
    Save current defaults to a file.
    
    Args:
        file_path: Path to save configuration file
        format: Format to save ('json' or 'yaml')
        
    Returns:
        bool: True if file was saved successfully
    """
    return _defaults_manager.save_file(file_path, format)