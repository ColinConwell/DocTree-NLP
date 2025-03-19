"""
Environment variable and API token discovery from various sources.

This module provides utilities for finding environment variables, API tokens,
and other configuration values from multiple sources including environment
variables, .env files, and interactive input.
"""
import os
import logging
import inspect
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List, Union

# Set up logging
logger = logging.getLogger(__name__)

# Detect execution environment
def _is_jupyter_notebook() -> bool:
    """
    Check if code is running in a Jupyter notebook.
    
    Returns:
        bool: True if in a Jupyter notebook
    """
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':  # Jupyter notebook or qtconsole
            return True
        elif shell == 'TerminalInteractiveShell':  # Terminal IPython
            return False
        else:
            return False
    except NameError:  # Not in an IPython environment
        return False

def _is_script() -> bool:
    """
    Check if code is running in a script (not in an interactive shell).
    
    Returns:
        bool: True if in a script
    """
    try:
        # Check if the code is being run from a script file
        for frame in inspect.stack():
            if frame.filename != '<stdin>' and not frame.filename.startswith('<ipython-'):
                return True
        return False
    except Exception:
        return False

def _load_dotenv_file(env_path: Path) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file
        
    Returns:
        Dict[str, str]: Dictionary of environment variables or empty dict if file not found
    """
    if not env_path.exists():
        return {}
    
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                    
                env_vars[key] = value
        
        logger.debug(f"Loaded environment variables from {env_path}")
        return env_vars
    except Exception as e:
        logger.warning(f"Error loading .env file {env_path}: {str(e)}")
        return {}

def _search_env_files(max_depth: int = 2) -> Dict[str, str]:
    """
    Search for .env files in current and parent directories.
    
    Args:
        max_depth: Maximum number of parent directories to search
        
    Returns:
        Dict[str, str]: Combined dictionary of all found environment variables
    """
    env_vars = {}
    
    # Start with current directory
    current_dir = Path.cwd()
    
    # Search current and parent directories
    for i in range(max_depth + 1):
        if i == 0:
            search_dir = current_dir
        else:
            search_dir = current_dir.parents[i-1]
        
        # Look for .env file in this directory
        env_path = search_dir / '.env'
        env_vars.update(_load_dotenv_file(env_path))
        
        # Also check for .env.local, .env.dev, etc.
        for variant in ['.env.local', '.env.dev', '.env.development']:
            env_path = search_dir / variant
            env_vars.update(_load_dotenv_file(env_path))
    
    return env_vars

def _get_console_input() -> Optional[str]:
    """
    Get API token from console input.
    
    Returns:
        Optional[str]: User provided token or None if cancelled
    """
    try:
        print("\nNotion API token not found in environment variables or .env files.")
        print("You can get your token from https://www.notion.so/my-integrations")
        print("Enter your Notion API token (press Enter to skip):")
        token = input("> ").strip()
        
        if token:
            print("\nWould you like to save this token to a .env file? (y/n)")
            save = input("> ").strip().lower()
            
            if save.startswith('y'):
                env_path = Path.cwd() / '.env'
                try:
                    # Check if file exists and append, otherwise create
                    if env_path.exists():
                        with open(env_path, 'a') as f:
                            f.write(f"\nNOTION_API_TOKEN={token}\n")
                    else:
                        with open(env_path, 'w') as f:
                            f.write(f"NOTION_API_TOKEN={token}\n")
                    print(f"Token saved to {env_path}")
                except Exception as e:
                    print(f"Failed to save token: {str(e)}")
            
            return token
        return None
    except (KeyboardInterrupt, EOFError):
        print("\nToken input cancelled.")
        return None

def _get_jupyter_input(description: str = "Enter API Token:", save_key: Optional[str] = "NOTION_API_TOKEN") -> Optional[str]:
    """
    Get input from Jupyter notebook input widget.
    
    Args:
        description: Description to show in the input widget
        save_key: Environment variable key to use when saving (if user chooses to save)
        
    Returns:
        Optional[str]: User provided value or None if cancelled
    """
    try:
        from ipywidgets import widgets
        from IPython.display import display
        
        # Default handling for Notion API token case
        if description == "Enter API Token:" and save_key == "NOTION_API_TOKEN":
            print("Notion API token not found in environment variables or .env files.")
            print("You can get your token from https://www.notion.so/my-integrations")
        
        # Create password input widget if it looks like a token/key, otherwise use text
        is_secret = any(substr in save_key.lower() for substr in ['token', 'key', 'secret', 'password'])
        
        if is_secret:
            value_input = widgets.Password(
                description=description,
                placeholder=f'Enter your {save_key}',
                style={'description_width': 'initial'},
                layout={'width': '50%'}
            )
        else:
            value_input = widgets.Text(
                description=description,
                placeholder=f'Enter value for {save_key}',
                style={'description_width': 'initial'},
                layout={'width': '50%'}
            )
        
        # Create save checkbox
        save_checkbox = widgets.Checkbox(
            value=False,
            description='Save to .env file',
            disabled=False
        )
        
        # Create submit button
        submit_button = widgets.Button(
            description='Submit',
            button_style='primary',
            tooltip='Submit your input'
        )
        
        # Create cancel button
        cancel_button = widgets.Button(
            description='Cancel',
            tooltip='Cancel input'
        )
        
        output = widgets.Output()
        
        # Variable to store result
        result = {'value': None}
        
        def on_submit_clicked(b):
            value = value_input.value.strip()
            save = save_checkbox.value
            
            if value:
                result['value'] = value
                
                if save and save_key:
                    env_path = Path.cwd() / '.env'
                    try:
                        # Check if file exists and append, otherwise create
                        if env_path.exists():
                            with open(env_path, 'a') as f:
                                f.write(f"\n{save_key}={value}\n")
                        else:
                            with open(env_path, 'w') as f:
                                f.write(f"{save_key}={value}\n")
                        with output:
                            print(f"Value saved to {env_path}")
                    except Exception as e:
                        with output:
                            print(f"Failed to save value: {str(e)}")
            
            submit_button.close()
            cancel_button.close()
            value_input.close()
            save_checkbox.close()
        
        def on_cancel_clicked(b):
            result['value'] = None
            submit_button.close()
            cancel_button.close()
            value_input.close()
            save_checkbox.close()
        
        submit_button.on_click(on_submit_clicked)
        cancel_button.on_click(on_cancel_clicked)
        
        # Display widgets
        display(value_input)
        display(save_checkbox)
        display(widgets.HBox([submit_button, cancel_button]))
        display(output)
        
        # Wait for user input
        while submit_button.layout.display != 'none' and cancel_button.layout.display != 'none':
            try:
                import time
                time.sleep(0.1)
            except KeyboardInterrupt:
                break
        
        return result['value']
    except ImportError:
        logger.warning("ipywidgets not installed. Falling back to console input.")
        return _get_console_input()
    except Exception as e:
        logger.error(f"Error getting Jupyter input: {str(e)}")
        return _get_console_input()

def find_notion_token() -> Optional[str]:
    """
    Find Notion API token from various sources.
    
    The function searches for a token in the following order:
    1. Environment variables
    2. .env files in current directory
    3. .env files in parent directories (up to specified depth)
    4. User input (console or Jupyter widget based on environment)
    
    Returns:
        Optional[str]: Notion API token or None if not found
    """
    token_keys = ['NOTION_API_TOKEN', 'NOTION_TOKEN', 'NOTION_KEY', 'NOTION_SECRET']
    
    # 1. Check environment variables
    for key in token_keys:
        token = os.environ.get(key)
        if token:
            logger.info(f"Found Notion API token in environment variable {key}")
            return token
    
    # 2 & 3. Search .env files in current and parent directories
    env_vars = _search_env_files(max_depth=2)
    for key in token_keys:
        if key in env_vars:
            logger.info(f"Found Notion API token in .env file with key {key}")
            return env_vars[key]
    
    # 4. Try to get token from user input
    if _is_jupyter_notebook():
        logger.info("Running in Jupyter notebook, using widget input")
        return _get_jupyter_input()
    elif _is_script():
        logger.info("Running in script, using console input")
        return _get_console_input()
    
    logger.warning("No Notion API token found and not in interactive environment")
    return None

# General Environment Variable Handling ------------------------------------------

class EnvLoader:
    """
    Handle environment variable loading from various sources including
    environment variables, .env files in current and parent directories,
    and interactive input when available.
    """
    
    def __init__(self, 
                 search_parent_dirs: bool = True, 
                 max_search_depth: int = 2,
                 allow_interactive: bool = True):
        """
        Initialize the environment loader.
        
        Args:
            search_parent_dirs: Whether to search parent directories for .env files
            max_search_depth: Maximum number of parent directories to search
            allow_interactive: Whether to allow interactive input for missing values
        """
        self.search_parent_dirs = search_parent_dirs
        self.max_search_depth = max_search_depth
        self.allow_interactive = allow_interactive
        self._env_cache = {}
        self._load_env_files()
    
    def _load_env_files(self):
        """Load environment variables from .env files."""
        # Load environment variables from .env files
        self._env_cache = _search_env_files(
            max_depth=self.max_search_depth if self.search_parent_dirs else 0
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get an environment variable from available sources.
        
        Args:
            key: Environment variable key
            default: Default value if key not found
            
        Returns:
            Value of environment variable or default
        """
        # Check environment variables first (highest priority)
        value = os.environ.get(key)
        if value is not None:
            logger.debug(f"Found {key} in environment variables")
            return value
        
        # Check loaded .env files
        if key in self._env_cache:
            logger.debug(f"Found {key} in .env files")
            return self._env_cache[key]
        
        # Try interactive input if allowed and appropriate
        if self.allow_interactive and (key.endswith('_TOKEN') or key.endswith('_API_KEY') or key.endswith('_KEY')):
            if _is_jupyter_notebook():
                logger.debug(f"Attempting to get {key} via Jupyter input")
                desc = key.replace('_', ' ').title()
                value = _get_interactive_input(
                    description=f"Enter {desc}:",
                    save_key=key
                )
                if value:
                    return value
            elif _is_script():
                logger.debug(f"Attempting to get {key} via console input")
                print(f"\n{key} not found in environment variables or .env files.")
                print(f"Enter {key} (press Enter to skip):")
                value = input("> ").strip()
                if value:
                    # Ask to save
                    print(f"\nWould you like to save {key} to a .env file? (y/n)")
                    save = input("> ").strip().lower()
                    if save.startswith('y'):
                        _save_to_env_file(key, value)
                    return value
        
        logger.debug(f"{key} not found in any source, using default: {default}")
        return default
    
    def get_required(self, key: str) -> str:
        """
        Get a required environment variable.
        
        Args:
            key: Environment variable key
            
        Returns:
            Value of environment variable
            
        Raises:
            ValueError: If environment variable is not found
        """
        value = self.get(key)
        if value is None:
            raise ValueError(f"Required environment variable {key} not found")
        return value
    
    def get_api_key(self, service: str) -> str:
        """
        Get an API key for a specific service.
        
        Args:
            service: Service name (e.g., 'openai', 'anthropic', 'notion')
            
        Returns:
            API key for the service
            
        Raises:
            ValueError: If API key is not found
        """
        # Standard naming convention for API keys
        key_name = f"{service.upper()}_API_KEY"
        
        # Try to get the API key with standard name
        api_key = self.get(key_name)
        
        if api_key is None:
            # Try alternative naming conventions
            alternative_names = [
                f"{service.upper()}_KEY",
                f"{service.upper()}_TOKEN",
                f"{service.upper()}_SECRET",
                f"{service.lower()}_api_key",
                f"{service.lower()}_token"
            ]
            
            for alt_name in alternative_names:
                api_key = self.get(alt_name)
                if api_key is not None:
                    logger.warning(
                        f"Using non-standard API key name: {alt_name}. "
                        f"Consider using {key_name} instead."
                    )
                    break
        
        if api_key is None:
            # For Notion, we have a specialized finder
            if service.lower() == 'notion':
                api_key = find_notion_token()
            
            # If still no API key, raise error
            if api_key is None:
                raise ValueError(f"API key for {service} not found. Set {key_name} environment variable.")
        
        return api_key

def _get_interactive_input(description: str, save_key: Optional[str] = None) -> Optional[str]:
    """
    Get value from interactive input (Jupyter widget or console).
    
    Args:
        description: Description to show to the user
        save_key: If provided, offer to save the value to .env file with this key
        
    Returns:
        Optional[str]: User provided value or None if cancelled
    """
    try:
        if _is_jupyter_notebook():
            return _get_jupyter_input(description=description, save_key=save_key)
        else:
            print(f"\n{description}")
            value = input("> ").strip()
            
            if value and save_key:
                print(f"\nWould you like to save this value as {save_key} to a .env file? (y/n)")
                save = input("> ").strip().lower()
                
                if save.startswith('y'):
                    _save_to_env_file(save_key, value)
            
            return value if value else None
    except (KeyboardInterrupt, EOFError):
        print("\nInput cancelled.")
        return None

def _save_to_env_file(key: str, value: str, env_path: Optional[Path] = None) -> None:
    """
    Save a key-value pair to a .env file.
    
    Args:
        key: Environment variable key
        value: Value to save
        env_path: Path to .env file (default: .env in current directory)
    """
    if env_path is None:
        env_path = Path.cwd() / '.env'
    
    try:
        # Check if file exists and append, otherwise create
        if env_path.exists():
            with open(env_path, 'a') as f:
                f.write(f"\n{key}={value}\n")
        else:
            with open(env_path, 'w') as f:
                f.write(f"{key}={value}\n")
        print(f"Value saved to {env_path}")
    except Exception as e:
        print(f"Failed to save to .env file: {str(e)}")

# Create a default instance for easy import
env_loader = EnvLoader()

def get_env(key: str, default: Any = None) -> Any:
    """
    Get an environment variable using the default loader.
    
    Args:
        key: Environment variable key
        default: Default value if key not found
        
    Returns:
        Value of environment variable or default
    """
    return env_loader.get(key, default)

def get_required_env(key: str) -> str:
    """
    Get a required environment variable using the default loader.
    
    Args:
        key: Environment variable key
        
    Returns:
        Value of environment variable
        
    Raises:
        ValueError: If environment variable is not found
    """
    return env_loader.get_required(key)

def get_api_key(service: str) -> str:
    """
    Get an API key for a specific service using the default loader.
    
    Args:
        service: Service name (e.g., 'openai', 'anthropic', 'notion')
        
    Returns:
        API key for the service
        
    Raises:
        ValueError: If API key is not found
    """
    return env_loader.get_api_key(service)