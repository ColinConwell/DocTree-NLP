"""
Example demonstrating use of alternative data sources (Obsidian and local files).

This example shows how to use the ObsidianClient and LocalSource 
clients to work with documents from sources other than Notion.
"""

import os
import tempfile
from pathlib import Path
from doctree_nlp.api_client import ObsidianClient, LocalSource
from doctree_nlp.defaults import get_default, set_default

# Create some sample markdown files for testing
def create_sample_files():
    """Create sample markdown files for testing."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")
    
    # Create some nested directories
    notes_dir = Path(temp_dir) / "notes"
    notes_dir.mkdir(exist_ok=True)
    
    projects_dir = Path(temp_dir) / "projects"
    projects_dir.mkdir(exist_ok=True)
    
    # Create some sample markdown files
    files = [
        (notes_dir / "meeting_notes.md", "# Meeting Notes\n\nDiscussed project timeline and deliverables."),
        (notes_dir / "ideas.md", "# Project Ideas\n\n- Build a better widget\n- Improve documentation"),
        (projects_dir / "project_a.md", "# Project A\n\n## Goals\n\nComplete by end of quarter."),
        (projects_dir / "project_b.md", "# Project B\n\n## Status\n\nIn progress."),
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

def obsidian_example(vault_path):
    """
    Example of working with Obsidian vault.
    
    Args:
        vault_path: Path to the Obsidian vault directory
    """
    print("\n===== OBSIDIAN CLIENT EXAMPLE =====")
    
    # Initialize the Obsidian client
    client = ObsidianClient(
        vault_path=vault_path,
        cache_enabled=True
    )
    
    # List all documents in the vault
    documents = client.list_documents()
    print(f"Found {len(documents)} documents in Obsidian vault:")
    
    for doc in documents:
        print(f"- {doc.title} (last modified: {doc.last_edited_time})")
    
    # Get a specific document (if available)
    if documents:
        doc_id = documents[0].id
        document = client.get_document(doc_id)
        print(f"\nDocument preview: {document.preview_text(200)}")

def local_files_example(directory_path):
    """
    Example of working with local markdown files.
    
    Args:
        directory_path: Path to the directory containing markdown files
    """
    print("\n===== LOCAL SOURCE CLIENT EXAMPLE =====")
    
    # Set a custom cache directory through defaults
    set_default('cache.directory', 'local_cache')
    set_default('cache.sources.local', 'local')
    
    # Initialize the local source client
    client = LocalSource(
        directory_path=directory_path,
        file_pattern="**/*.md",  # All markdown files in all subdirectories
    )
    
    # List all matching documents
    documents = client.list_documents()
    print(f"Found {len(documents)} documents in directory:")
    
    for doc in documents:
        print(f"- {doc.title} ({doc.id}, created: {doc.created_time})")
    
    # Get a specific document (if available)
    if documents:
        doc_id = documents[0].id
        document = client.get_document(doc_id)
        print(f"\nDocument ID: {document.id}")
        print(f"Document title: {document.title}")
        print(f"Document source: {document.source_id}")
        print(f"Document blocks: {len(document.blocks)}")
        
        if document.blocks:
            print(f"\nFirst block type: {document.blocks[0].type}")
            print(f"First block content preview: {document.blocks[0].content[:50]}...")
            
            if document.tree:
                print("\nDocument has a document tree structure")


def combined_doctree_example(directory_path):
    """
    Example of working with local files as a single DocTree.
    
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
    print(f"Found {len(documents)} document(s) in combined mode:")
    
    for doc in documents:
        print(f"- {doc.title} ({doc.id})")
    
    # Get the combined document
    if documents:
        combined_doc = client.get_document(documents[0].id)
        print(f"\nCombined document ID: {combined_doc.id}")
        print(f"Combined document title: {combined_doc.title}")
        print(f"Total blocks: {len(combined_doc.blocks)}")
        
        # Display the hierarchical structure
        if combined_doc.tree:
            print("\nDocument tree structure:")
            
            # Show the first few heading blocks to demonstrate the hierarchy
            heading_count = 0
            for block in combined_doc.blocks:
                if block.type.startswith('heading_'):
                    indent = "  " * block.indent_level
                    print(f"{indent}{block.type}: {block.content}")
                    heading_count += 1
                    if heading_count >= 10:  # Limit the output
                        print("... more headings ...")
                        break

if __name__ == "__main__":
    # Create temporary files for demonstration
    temp_dir = create_sample_files()
    
    try:
        # Demonstrate working with a directory as if it's an Obsidian vault
        obsidian_example(temp_dir)
        
        # Demonstrate working with a directory of markdown files
        local_files_example(temp_dir)
        
        # Demonstrate working with a directory as a single combined DocTree
        combined_doctree_example(temp_dir)
    
    finally:
        # Always clean up temporary files
        clean_up(temp_dir)