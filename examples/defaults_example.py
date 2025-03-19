"""
Example demonstrating the new defaults configuration system in NotioNLPToolkit.

This script demonstrates how to use the defaults system to customize the toolkit's
behavior and how to load and save configuration files.
"""

import os
import json
from pathlib import Path
from pprint import pprint

from notionlp import (
    get_defaults, get_default, set_default, update_defaults,
    load_defaults_from_env, load_defaults_from_file, save_defaults_to_file,
    NotionClient
)

def show_current_defaults():
    """Show current default values."""
    print("\n=== Current Default Configuration ===")
    defaults = get_defaults().to_dict()
    
    # Show in a more readable format
    for section, values in defaults.items():
        print(f"\n[{section}]")
        for key, value in values.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for subkey, subvalue in value.items():
                    print(f"    {subkey}: {subvalue}")
            else:
                print(f"  {key}: {value}")

def update_via_individual_settings():
    """Demonstrate updating individual settings."""
    print("\n=== Updating Individual Settings ===")
    
    # Get current values first
    print(f"Current cache directory: {get_default('cache.directory')}")
    print(f"Current window size: {get_default('document.window_size')}")
    
    # Update values
    set_default('cache.directory', 'custom_cache')
    set_default('document.window_size', 30)
    
    # Show updated values
    print(f"Updated cache directory: {get_default('cache.directory')}")
    print(f"Updated window size: {get_default('document.window_size')}")
    
    # Demonstrate nested updates
    print(f"Current internal source: {get_default('cache.sources.internal')}")
    set_default('cache.sources.internal', 'processed')
    print(f"Updated internal source: {get_default('cache.sources.internal')}")

def update_via_dictionary():
    """Demonstrate updating settings via dictionary."""
    print("\n=== Updating Settings via Dictionary ===")
    
    # Current settings
    print(f"Current API version: {get_default('api.version')}")
    print(f"Current rate limit: {get_default('api.rate_limit')}")
    
    # Update with a dictionary
    update_defaults({
        'api': {
            'version': '2023-01-01',
            'rate_limit': 5
        }
    })
    
    # Show updated values
    print(f"Updated API version: {get_default('api.version')}")
    print(f"Updated rate limit: {get_default('api.rate_limit')}")

def save_and_load_config():
    """Demonstrate saving and loading configuration files."""
    print("\n=== Saving and Loading Configuration ===")
    
    # Create a temporary directory for configs
    config_dir = Path("./config_example")
    config_dir.mkdir(exist_ok=True)
    
    # Save current config to JSON and YAML
    json_path = config_dir / "config.json"
    yaml_path = config_dir / "config.yaml"
    
    save_defaults_to_file(json_path, 'json')
    save_defaults_to_file(yaml_path, 'yaml')
    
    print(f"Saved configuration to {json_path} and {yaml_path}")
    
    # Modify a setting
    original_window_size = get_default('document.window_size')
    set_default('document.window_size', 100)
    print(f"Changed window size from {original_window_size} to {get_default('document.window_size')}")
    
    # Load config back from file
    load_defaults_from_file(json_path)
    print(f"Loaded config from JSON, window size is now: {get_default('document.window_size')}")
    
    # Clean up
    print("Cleaning up example files...")
    try:
        os.remove(json_path)
        os.remove(yaml_path)
        os.rmdir(config_dir)
    except Exception as e:
        print(f"Error cleaning up: {str(e)}")

def load_from_env():
    """Demonstrate loading settings from environment variables."""
    print("\n=== Loading Settings from Environment Variables ===")
    
    # Save original values
    original_cache_dir = get_default('cache.directory')
    
    # Set environment variables
    os.environ["NOTIONLP_CACHE_DIRECTORY"] = "env_cache"
    
    # Load from environment
    load_defaults_from_env()
    
    # Show updated values
    print(f"Cache directory updated from '{original_cache_dir}' to '{get_default('cache.directory')}'")
    
    # Clean up
    del os.environ["NOTIONLP_CACHE_DIRECTORY"]

def show_impact_on_client():
    """Demonstrate how defaults affect client initialization."""
    print("\n=== Impact on NotionClient ===")
    
    # Save original values
    original_cache_dir = get_default('cache.directory')
    
    # Set a custom cache directory
    set_default('cache.directory', 'client_example_cache')
    
    # Create a client that uses the defaults
    client = NotionClient("dummy_token")
    
    # Show how it affects the client
    print(f"Set default cache.directory to: {get_default('cache.directory')}")
    print(f"Client's cache_manager.cache_dir includes: {client.cache_manager.cache_dir}")
    
    # Restore original value
    set_default('cache.directory', original_cache_dir)

def run_examples():
    """Run all examples."""
    # Save initial defaults to restore later
    original_defaults = get_defaults().to_dict()
    
    try:
        show_current_defaults()
        update_via_individual_settings()
        update_via_dictionary()
        save_and_load_config()
        load_from_env()
        show_impact_on_client()
    finally:
        # Restore original defaults
        update_defaults(original_defaults)
        print("\n=== Examples Complete ===")
        print("Original defaults have been restored.")

if __name__ == "__main__":
    run_examples()