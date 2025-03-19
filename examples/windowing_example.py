"""
Example demonstrating document windowing functionality in DocTree-NLP library.

This script demonstrates how to use DocumentWindower and TreeWindower
to efficiently navigate and display large documents.
"""

import time
import logging
from pathlib import Path
from datetime import datetime

from doctree_nlp.api_client import NotionClient
from doctree_nlp.structure import Document, Block
from doctree_nlp.windowing import DocumentWindower, TreeWindower
from doctree_nlp.lazy_document import LazyDocument, create_lazy_document

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def basic_windowing_example():
    """Demonstrate basic document windowing functionality."""
    print("\n=== Basic Document Windowing ===")
    
    # Initialize client and get a document
    client = NotionClient()
    documents = client.list_documents()
    
    if not documents:
        print("No documents found!")
        return
    
    print(f"Found {len(documents)} documents")
    
    # Get a document with content
    document, blocks = client.get_document_content(documents[0].id)
    
    if not document or not blocks:
        print("Failed to load document content!")
        return
    
    document.blocks = blocks
    print(f"Loaded document: {document.title} with {len(document.blocks)} blocks")
    
    # Create a document windower
    windower = DocumentWindower(default_window_size=10)
    
    # Create the first window
    window = windower.create_window(document)
    print(f"\nWindow 1: Blocks {window.start_index}-{window.end_index} of {window.total_blocks}")
    print(f"Contains {len(window.blocks)} blocks")
    
    # Display first few blocks in the window
    for i, block in enumerate(window.blocks[:3]):
        print(f"  Block {i}: {block.type} - {block.content[:50]}...")
    
    if window.has_next:
        # Get the next window
        next_window = windower.get_next_window(window, document)
        print(f"\nWindow 2: Blocks {next_window.start_index}-{next_window.end_index} of {next_window.total_blocks}")
        print(f"Contains {len(next_window.blocks)} blocks")
        
        # Display first few blocks in the next window
        for i, block in enumerate(next_window.blocks[:3]):
            print(f"  Block {i}: {block.type} - {block.content[:50]}...")
    
    # Generate all windows
    all_windows = list(windower.generate_all_windows(document, window_size=20))
    print(f"\nDocument can be divided into {len(all_windows)} windows of 20 blocks each")
    
    # Find a window containing specific text
    search_text = "the"  # Common word likely to be found
    text_window = windower.find_text_window(document, search_text, context_blocks=2)
    
    if text_window:
        print(f"\nFound window containing '{search_text}':")
        print(f"Window: Blocks {text_window.start_index}-{text_window.end_index} of {text_window.total_blocks}")
        
        # Find and display the matching block
        for block in text_window.blocks:
            if search_text.lower() in block.content.lower():
                print(f"  Matching block: {block.type} - {block.content[:100]}...")
                break
    else:
        print(f"\nNo window found containing '{search_text}'")


def tree_windowing_example():
    """Demonstrate tree-based document windowing."""
    print("\n=== Tree-Based Document Windowing ===")
    
    # Initialize client and get a document
    client = NotionClient()
    documents = client.list_documents()
    
    if not documents:
        print("No documents found!")
        return
    
    # Get a document with content
    document, blocks = client.get_document_content(documents[0].id)
    
    if not document or not blocks:
        print("Failed to load document content!")
        return
    
    document.blocks = blocks
    
    # Build the document tree
    document.build_tree()
    print(f"Built tree for document: {document.title}")
    
    # Create a tree windower
    tree_windower = TreeWindower(default_nodes_per_window=10)
    
    # Create a window into the tree
    window_nodes, has_previous, has_next = tree_windower.window_tree(document)
    
    print(f"\nTree window contains {len(window_nodes)} nodes")
    print(f"Has previous: {has_previous}, Has next: {has_next}")
    
    # Display some nodes in the window
    for i, node in enumerate(window_nodes[:5]):
        print(f"  Node {i}: {node.block.type} - {node.block.content[:50]}...")
        print(f"    Children: {len(node.children)}")
    
    if has_next:
        # Get the next window
        next_offset = 10  # Size of previous window
        next_window_nodes, has_prev, has_next = tree_windower.window_tree(document, offset=next_offset)
        
        print(f"\nNext tree window contains {len(next_window_nodes)} nodes")
        print(f"Has previous: {has_prev}, Has next: {has_next}")
        
        # Display some nodes in the window
        for i, node in enumerate(next_window_nodes[:3]):
            print(f"  Node {i}: {node.block.type} - {node.block.content[:50]}...")
            print(f"    Children: {len(node.children)}")
    
    # Try to find a specific node window
    if len(document.blocks) > 0:
        target_block_id = document.blocks[min(15, len(document.blocks) - 1)].id
        node_window, has_prev, has_next = tree_windower.find_node_window(
            document, target_block_id, context_nodes=2
        )
        
        print(f"\nFound window for node {target_block_id}:")
        print(f"Window contains {len(node_window)} nodes")
        print(f"Has previous: {has_prev}, Has next: {has_next}")


def lazy_windowing_example():
    """Demonstrate windowing with lazy documents."""
    print("\n=== Lazy Document Windowing ===")
    
    # Initialize client
    client = NotionClient()
    
    # Get a document list
    documents = client.list_documents()
    
    if not documents:
        print("No documents found!")
        return
    
    # Create a lazy document
    lazy_doc = create_lazy_document(documents[0].id, client)
    
    if not lazy_doc:
        print("Failed to create lazy document!")
        return
    
    print(f"Created lazy document: {lazy_doc.title}")
    
    # Create windower
    windower = DocumentWindower(default_window_size=10)
    
    # Create a window - this will trigger loading of blocks
    start_time = time.time()
    window = windower.create_window(lazy_doc)
    time_taken = time.time() - start_time
    
    print(f"\nCreated window in {time_taken:.2f} seconds")
    print(f"Window: Blocks {window.start_index}-{window.end_index} of {window.total_blocks}")
    print(f"Contains {len(window.blocks)} blocks")
    
    # Display a window as markdown
    markdown = window.to_markdown()
    print(f"\nWindow Markdown (first 200 chars):\n{markdown[:200]}...")
    
    # Get the next window
    if window.has_next:
        start_time = time.time()
        next_window = windower.get_next_window(window, lazy_doc)
        time_taken = time.time() - start_time
        
        print(f"\nCreated next window in {time_taken:.2f} seconds")
        print(f"Next window: Blocks {next_window.start_index}-{next_window.end_index} of {next_window.total_blocks}")


def pagination_example():
    """Demonstrate pagination through a large document."""
    print("\n=== Document Pagination Example ===")
    
    # Initialize client and get a document
    client = NotionClient()
    documents = client.list_documents()
    
    if not documents:
        print("No documents found!")
        return
    
    # Find a document with a reasonable number of blocks
    target_doc = None
    for doc in documents:
        document, blocks = client.get_document_content(doc.id)
        if len(blocks) >= 30:
            document.blocks = blocks
            target_doc = document
            break
    
    if not target_doc:
        print("No document with sufficient blocks found!")
        return
    
    print(f"Using document: {target_doc.title} with {len(target_doc.blocks)} blocks")
    
    # Create windower with small page size for demonstration
    windower = DocumentWindower(default_window_size=10)
    
    # Paginate through the document
    page_num = 1
    window = windower.create_window(target_doc)
    
    while True:
        print(f"\nPage {page_num}: Blocks {window.start_index}-{window.end_index} of {window.total_blocks}")
        print(f"Contains {len(window.blocks)} blocks")
        
        # Display first block in this page
        if window.blocks:
            print(f"  First block: {window.blocks[0].type} - {window.blocks[0].content[:50]}...")
        
        # Check if there are more pages
        if not window.has_next:
            print("Reached the end of the document.")
            break
        
        # Get next page
        window = windower.get_next_window(window, target_doc)
        page_num += 1
        
        # Limit to 5 pages for demonstration
        if page_num > 5:
            print("Stopping after 5 pages...")
            break


def window_navigation_example():
    """Demonstrate window navigation features."""
    print("\n=== Window Navigation Example ===")
    
    # Initialize client and get a document
    client = NotionClient()
    documents = client.list_documents()
    
    if not documents:
        print("No documents found!")
        return
    
    # Get a document with content
    document, blocks = client.get_document_content(documents[0].id)
    
    if not document or not blocks:
        print("Failed to load document content!")
        return
    
    document.blocks = blocks
    print(f"Loaded document: {document.title} with {len(document.blocks)} blocks")
    
    # Create a document windower
    windower = DocumentWindower(default_window_size=5)
    
    # Navigation simulation
    print("\nSimulating document navigation:")
    
    # Start with the first window
    current_window = windower.create_window(document)
    print(f"Starting at: Blocks {current_window.start_index}-{current_window.end_index}")
    
    # Navigate forward twice
    if current_window.has_next:
        current_window = windower.get_next_window(current_window, document)
        print(f"Forward to: Blocks {current_window.start_index}-{current_window.end_index}")
    
    if current_window.has_next:
        current_window = windower.get_next_window(current_window, document)
        print(f"Forward to: Blocks {current_window.start_index}-{current_window.end_index}")
    
    # Navigate back once
    if current_window.has_previous:
        current_window = windower.get_previous_window(current_window, document)
        print(f"Back to: Blocks {current_window.start_index}-{current_window.end_index}")
    
    # Jump to a specific position by creating a new window
    jump_offset = min(20, len(document.blocks) - 5)
    current_window = windower.create_window(document, offset=jump_offset)
    print(f"Jump to: Blocks {current_window.start_index}-{current_window.end_index}")
    
    # Search for content
    search_window = windower.find_text_window(document, "the", window_size=5)
    if search_window:
        print(f"Search found: Blocks {search_window.start_index}-{search_window.end_index}")
    
    print("\nNavigation example complete!")


def run_all_examples():
    """Run all windowing examples."""
    basic_windowing_example()
    tree_windowing_example()
    lazy_windowing_example()
    pagination_example()
    window_navigation_example()


if __name__ == "__main__":
    run_all_examples()