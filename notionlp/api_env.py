import logging
import os
from typing import Optional, Any
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Environment Variable Loading ----------------------------------------------------

DOTENV_AVAILABLE = False

def _load_dotenv():
    """Load the .env file if it exists."""
    global DOTENV_AVAILABLE

    try:
        from dotenv import load_dotenv
        DOTENV_AVAILABLE = True
    except ImportError:
        DOTENV_AVAILABLE = False
        logger.info("python-dotenv not installed. .env file loading will be unavailable.")

class EnvLoader:
    """Handle environment variable loading from various sources."""
    
    def __init__(self, load_dotenv_file: bool = True, dotenv_path: Optional[str] = None):
        """
        Initialize the environment loader.
        
        Args:
            load_dotenv_file: Whether to attempt loading from .env file
            dotenv_path: Path to .env file (default: search in current directory)
        """
        self.sources = []
        
        # Add environment variables as a source
        self.sources.append(("environment", os.environ))
        
        # Try to load from .env file if requested
        if load_dotenv_file and DOTENV_AVAILABLE:
            load_dotenv(dotenv_path=dotenv_path)
            logger.info(f"Loaded environment variables from .env file: {dotenv_path or '.env'}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get an environment variable from available sources.
        
        Args:
            key: Environment variable key
            default: Default value if key not found
            
        Returns:
            Value of environment variable or default
        """
        for source_name, source in self.sources:
            if key in source:
                logger.debug(f"Found {key} in {source_name}")
                return source[key]
        
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
            service: Service name (e.g., 'openai', 'anthropic')
            
        Returns:
            API key for the service
            
        Raises:
            ValueError: If API key is not found
        """
        # Standard naming convention for API keys
        key_name = f"{service.upper()}_API_KEY"
        
        # Try to get the API key
        api_key = self.get(key_name)
        
        if api_key is None:
            # Try alternative naming conventions
            alternative_names = [
                f"{service.upper()}_KEY",
                f"{service.upper()}_SECRET",
                f"{service.lower()}_api_key"
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
            raise ValueError(f"API key for {service} not found. Set {key_name} environment variable.")
        
        return api_key

# Create a default instance for easy import
env = EnvLoader()

def get_env(key: str, default: Any = None) -> Any:
    """
    Get an environment variable using the default loader.
    
    Args:
        key: Environment variable key
        default: Default value if key not found
        
    Returns:
        Value of environment variable or default
    """
    return env.get(key, default)

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
    return env.get_required(key)

def get_api_key(service: str) -> str:
    """
    Get an API key for a specific service using the default loader.
    
    Args:
        service: Service name (e.g., 'openai', 'anthropic')
        
    Returns:
        API key for the service
        
    Raises:
        ValueError: If API key is not found
    """
    return env.get_api_key(service)