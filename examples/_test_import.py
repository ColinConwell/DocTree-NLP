"""
Test script to demonstrate importing and using main functions from example files.
"""
import examples

def main():
    # Print all available example functions using list_example_options
    print("Available example functions:")
    for func_name in examples.list_example_options():
        print(f"  - {func_name}")
    
    # Example of how to call a specific example function directly
    print("\nMethod 1: Call the function directly:")
    print("  examples.basic_usage()")
    
    # Example of how to use run_example
    print("\nMethod 2: Use run_example function:")
    print("  examples.run_example('basic_usage')")
    
    # Demonstrate running an example (uncomment to actually run)
    print("\nDemonstration (uncomment in code to run):")
    print("# Running basic_usage example:")
    # examples.run_example('basic_usage')
    
    # Demonstrate error handling
    print("\nError handling example:")
    try:
        print("Trying to run non-existent example:")
        # examples.run_example('non_existent_example')
        print("  examples.run_example('non_existent_example')")
    except ValueError as e:
        print(f"  This would raise: {e}")

if __name__ == "__main__":
    main()