import os, importlib
from typing import Dict, Callable, Any

# Dictionary to store all main functions
EXAMPLE_FUNCTIONS: Dict[str, Callable[[], Any]] = {}

# Import all main() modules in the examples directory
for file in os.listdir(os.path.dirname(__file__)):
    if file.endswith('.py') and not file.startswith('_'):
        module_name = file[:-3]

        try: # to import the module
            module = importlib.import_module(f'examples.{module_name}')
            
            # If the module has a main function, add it to our dictionary
            if hasattr(module, 'main') and callable(module.main):
                EXAMPLE_FUNCTIONS[module_name] = module.main
                
                # Also make available at package level with module name
                globals()[module_name] = module.main

        except Exception as error:
            print(f"Error importing {module_name}: {error}")

def list_example_options():
    """
    List all available example functions.
    
    Returns:
        List of example function names
    """
    return list(EXAMPLE_FUNCTIONS.keys())

def run_example(example_name):
    """
    Run a specific example by name.
    
    Args:
        example_name (str): The name of the example to run (without .py extension)
        
    Returns:
        The result of the example function, or None if the example doesn't exist
        
    Raises:
        ValueError: If the example name doesn't exist
    """
    if example_name in EXAMPLE_FUNCTIONS:
        return EXAMPLE_FUNCTIONS[example_name]()
    else:
        available = list(EXAMPLE_FUNCTIONS.keys())
        raise ValueError(f"Example '{example_name}' not found. Available examples: {available}")

# List of all example modules
__all__ = ['run_example', 'list_example_options'] + list(EXAMPLE_FUNCTIONS.keys())
