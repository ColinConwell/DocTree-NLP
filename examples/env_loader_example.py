"""
Example showing advanced environment variable handling with EnvLoader.

This example demonstrates how to use the EnvLoader for managing environment 
variables, API keys, and configuration values with interactive input support.
"""
from doctree_nlp import EnvLoader, get_env, get_required_env, get_api_key

def main():
    """Demonstrate environment variable loading features."""
    print("=== Environment Variable Loading Demo ===\n")
    
    # 1. Basic environment variable access
    print("1. Basic Environment Variable Access:")
    host = get_env("DATABASE_HOST", "localhost")
    port = get_env("DATABASE_PORT", "5432")
    print(f"  • DATABASE_HOST = {host}")
    print(f"  • DATABASE_PORT = {port}")
    
    # 2. Interactive input - Service API keys
    print("\n2. API Key Discovery:")
    try:
        # This will check environment variables like OPENAI_API_KEY
        # If not found, it will prompt the user for input
        openai_key = get_api_key("openai")
        # Display only first/last few chars for security
        masked_key = openai_key[:4] + "..." + openai_key[-4:] if len(openai_key) > 8 else "***"
        print(f"  • Found OpenAI API key: {masked_key}")
    except ValueError:
        print("  • OpenAI API key not provided. Skipping this step.")
    
    # 3. Create a custom environment loader
    print("\n3. Custom Environment Loader:")
    custom_loader = EnvLoader(
        search_parent_dirs=True,     # Look in parent directories
        max_search_depth=2,          # Up to 2 levels up
        allow_interactive=True       # Allow interactive prompts
    )
    
    # Demo custom loader
    print("  • Custom loader is looking for APP_CONFIG (with interactive input)")
    app_config = custom_loader.get("APP_CONFIG", "default-config")
    print(f"  • APP_CONFIG = {app_config}")
    
    print("\nThat's it! The environment loader makes it easy to find and manage configuration values.")
    print("It supports environment variables, .env files, and interactive input when needed.")

if __name__ == "__main__":
    main()