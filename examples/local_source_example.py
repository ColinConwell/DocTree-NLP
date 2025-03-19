"""
Example demonstrating the LocalSource client with single DocTree handling.

This example shows how to use the LocalSource client to work with local
markdown files as individual documents or as a single hierarchical DocTree.
"""

import os
import tempfile
from pathlib import Path
from doctree_nlp.api_client import LocalSource
from doctree_nlp.defaults import get_default, set_default

# Create some sample markdown files for testing
def create_sample_files():
    """Create sample markdown files with nested directories for testing."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")
    
    # Create nested directories
    docs_dir = Path(temp_dir) / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    api_dir = docs_dir / "api"
    api_dir.mkdir(exist_ok=True)
    
    tutorials_dir = docs_dir / "tutorials"
    tutorials_dir.mkdir(exist_ok=True)
    
    advanced_dir = tutorials_dir / "advanced"
    advanced_dir.mkdir(exist_ok=True)
    
    # Create sample markdown files with richer content
    files = [
        (Path(temp_dir) / "README.md", """# Project Documentation

This is a sample project to demonstrate DocTree functionality.

## Overview

- Documentation is in the `/docs` directory
- API documentation is in `/docs/api`
- Tutorials are in `/docs/tutorials`

## Getting Started

Check out our tutorials to get started quickly.
"""),
        (docs_dir / "index.md", """# Documentation Home

Welcome to the documentation for our project.

## Sections

1. [API Reference](./api/index.md)
2. [Tutorials](./tutorials/index.md)
"""),
        (api_dir / "index.md", """# API Reference

## Classes

- `DocTree`: The main document tree class
- `Document`: Represents a single document
- `Block`: Basic content block

## Methods

- `get_document()`: Retrieve a document
- `list_documents()`: List all available documents
"""),
        (tutorials_dir / "index.md", """# Tutorials

Learn how to use our project with these step-by-step tutorials:

## Basic Tutorials

- [Getting Started](./getting_started.md)
- [Configuration](./configuration.md)

## Advanced Topics

See the [advanced](./advanced/) section for more complex tutorials.
"""),
        (tutorials_dir / "getting_started.md", """# Getting Started

This tutorial will guide you through the initial setup.

## Installation

```
pip install doctree-nlp
```

## Basic Usage

```python
from doctree_nlp import DocTree

# Create a new document tree
tree = DocTree()
```
"""),
        (advanced_dir / "customization.md", """# Custom Configuration

## Advanced Settings

You can customize the behavior with these settings:

- `cache_enabled`: Enable or disable caching
- `source_as_single_doctree`: Treat all files as a single document

## Example

```python
client = LocalSource(
    directory_path="/path/to/docs",
    source_as_single_doctree=True
)
```
"""),
    ]
    
    for path, content in files:
        with open(path, 'w') as f:
            f.write(content)
        print(f"Created file: {path}")
    
    return temp_dir

def clean_up(directory):
    """Remove temporary directory and files."""
    import shutil
    shutil.rmtree(directory, ignore_errors=True)
    print(f"Removed temporary directory: {directory}")

def individual_files_example(directory_path):
    """
    Example of working with local markdown files as individual documents.
    
    Args:
        directory_path: Path to the directory containing markdown files
    """
    print("\n===== INDIVIDUAL FILES EXAMPLE =====")
    
    # Initialize the local source client with default settings
    client = LocalSource(
        directory_path=directory_path,
        file_pattern="**/*.md",  # All markdown files in all subdirectories
    )
    
    # List all matching documents
    documents = client.list_documents()
    print(f"Found {len(documents)} individual documents:")
    
    for doc in documents:
        print(f"- {doc.title} ({doc.id})")
    
    # Get a specific document
    if documents:
        # Get the README.md document if available
        readme_doc = None
        for doc in documents:
            if doc.id.endswith("README.md"):
                readme_doc = doc
                break
                
        if readme_doc:
            document = client.get_document(readme_doc.id)
            print(f"\nDocument: {document.title}")
            print(f"Blocks: {len(document.blocks)}")
            
            # Display block types in the document
            block_types = {}
            for block in document.blocks:
                if block.type not in block_types:
                    block_types[block.type] = 0
                block_types[block.type] += 1
            
            print("Block types:")
            for block_type, count in block_types.items():
                print(f"  - {block_type}: {count}")
            
            # Show document preview
            print(f"\nPreview: {document.preview_sentences(2)}...")
            
            # Convert to markdown
            print("\nMarkdown representation:")
            print(document.to_markdown()[:500] + "..." if len(document.to_markdown()) > 500 else document.to_markdown())

def combined_doctree_example(directory_path):
    """
    Example of working with local files as a single hierarchical DocTree.
    
    Args:
        directory_path: Path to the directory containing markdown files
    """
    print("\n===== COMBINED DOCTREE EXAMPLE =====")
    
    # Initialize the local source client with source_as_single_doctree=True
    client = LocalSource(
        directory_path=directory_path,
        file_pattern="**/*.md",
        source_as_single_doctree=True
    )
    
    # List all documents (should only be one combined document)
    documents = client.list_documents()
    print(f"Found {len(documents)} document(s) in combined mode")
    
    # Get the combined document
    if documents:
        combined_doc = client.get_document(documents[0].id)
        print(f"Combined document title: {combined_doc.title}")
        print(f"Total blocks: {len(combined_doc.blocks)}")
        
        # Count blocks by type
        block_types = {}
        heading_levels = {}
        
        for block in combined_doc.blocks:
            if block.type not in block_types:
                block_types[block.type] = 0
            block_types[block.type] += 1
            
            # Track heading levels to understand the document hierarchy
            if block.type.startswith("heading_"):
                level = int(block.type[-1])
                if level not in heading_levels:
                    heading_levels[level] = 0
                heading_levels[level] += 1
        
        # Display block type statistics
        print("\nBlock types:")
        for block_type, count in sorted(block_types.items()):
            print(f"  - {block_type}: {count}")
        
        # Display heading level statistics to show hierarchy
        if heading_levels:
            print("\nDocument hierarchy (heading levels):")
            for level in sorted(heading_levels.keys()):
                print(f"  - Level {level}: {heading_levels[level]} headings")
        
        # Display the hierarchical structure
        print("\nDocument structure preview:")
        heading_blocks = [b for b in combined_doc.blocks if b.type.startswith('heading_')]
        
        # Show just a sample of the structure (first 15 headings)
        for i, block in enumerate(heading_blocks[:15]):
            if block.type.startswith('heading_'):
                indent = "  " * block.indent_level
                level = block.type[-1]  # Extract the heading level number
                print(f"{indent}H{level}: {block.content}")
                
        if len(heading_blocks) > 15:
            print("... more headings ...")
            
        # Display how many nested levels of content we have
        max_indent = max([b.indent_level for b in combined_doc.blocks]) if combined_doc.blocks else 0
        print(f"\nMaximum nesting level: {max_indent}")

if __name__ == "__main__":
    # Create temporary files for demonstration
    temp_dir = create_sample_files()
    
    try:
        # Demonstrate working with individual files
        individual_files_example(temp_dir)
        
        # Demonstrate working with a directory as a single combined DocTree
        combined_doctree_example(temp_dir)
        
        print("\nNote: You can pass directory_path=None to have LocalSource prompt you for a directory at runtime.")
    
    finally:
        # Always clean up temporary files
        clean_up(temp_dir)