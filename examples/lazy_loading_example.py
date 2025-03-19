"""
Example demonstrating lazy loading functionality in DocTree NLP Toolkit.

This script demonstrates how to use LazyDocument and LazyDocumentCollection
to efficiently handle large document collections with minimal memory usage.
"""

import time
import logging
import psutil
from pathlib import Path
from datetime import datetime

from doctree_nlp.api_client import NotionClient
from doctree_nlp.lazy_document import LazyDocument, LazyDocumentCollection, create_lazy_document
from doctree_nlp.structure import Document, Block

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_memory_usage(message):
    """Print current memory usage."""
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"{message}: {memory_info.rss / (1024 * 1024):.2f} MB")


def standard_document_example():
    """Demonstrate standard document loading."""
    print("\n=== Standard Document Loading ===")
    print_memory_usage("Initial memory")
    
    client = NotionClient()
    
    # Get list of documents
    start_time = time.time()
    documents = client.list_documents()
    list_time = time.time() - start_time
    print(f"Listed {len(documents)} documents in {list_time:.2f} seconds")
    print_memory_usage("After listing documents")
    
    # Load each document fully
    loaded_documents = []
    start_time = time.time()
    
    for doc in documents[:5]:  # Load first 5 documents
        document = client.get_document(doc.id)
        loaded_documents.append(document)
        print(f"Loaded document: {document.title} ({len(document.blocks)} blocks)")
    
    load_time = time.time() - start_time
    print(f"Loaded {len(loaded_documents)} documents in {load_time:.2f} seconds")
    print_memory_usage("After loading documents")
    
    # Process documents (build trees, convert to markdown)
    start_time = time.time()
    for document in loaded_documents:
        if not document.tree:
            document.build_tree()
        markdown = document.to_markdown()
        print(f"Processed document: {document.title} ({len(markdown)} chars)")
    
    process_time = time.time() - start_time
    print(f"Processed {len(loaded_documents)} documents in {process_time:.2f} seconds")
    print_memory_usage("After processing documents")
    
    return {
        "list_time": list_time,
        "load_time": load_time,
        "process_time": process_time,
        "document_count": len(loaded_documents)
    }


def lazy_document_example():
    """Demonstrate lazy document loading."""
    print("\n=== Lazy Document Loading ===")
    print_memory_usage("Initial memory")
    
    client = NotionClient()
    
    # Create a lazy document collection (only loads metadata)
    start_time = time.time()
    collection = LazyDocumentCollection(client, preload_metadata=True)
    list_time = time.time() - start_time
    print(f"Preloaded metadata for {len(collection.documents)} documents in {list_time:.2f} seconds")
    print_memory_usage("After preloading metadata")
    
    # Get the same documents as in the standard example
    lazy_documents = []
    document_ids = list(collection.documents.keys())[:5]  # First 5 documents
    
    start_time = time.time()
    for doc_id in document_ids:
        lazy_doc = collection.get_document(doc_id)
        lazy_documents.append(lazy_doc)
        print(f"Got lazy document: {lazy_doc.title} (blocks not loaded yet)")
    
    get_time = time.time() - start_time
    print(f"Got {len(lazy_documents)} lazy documents in {get_time:.2f} seconds")
    print_memory_usage("After getting lazy documents")
    
    # Process documents (this will trigger loading as needed)
    start_time = time.time()
    for document in lazy_documents:
        # This will trigger block loading and tree building as needed
        markdown = document.to_markdown()
        print(f"Processed document: {document.title} ({len(markdown)} chars)")
    
    process_time = time.time() - start_time
    print(f"Processed {len(lazy_documents)} documents in {process_time:.2f} seconds")
    print_memory_usage("After processing documents")
    
    # Clear content to free memory
    collection.clear_loaded_content(keep_metadata=True)
    print_memory_usage("After clearing content")
    
    return {
        "list_time": list_time,
        "get_time": get_time,
        "process_time": process_time,
        "document_count": len(lazy_documents)
    }


def search_example():
    """Demonstrate efficient document searching with lazy loading."""
    print("\n=== Document Search with Lazy Loading ===")
    print_memory_usage("Initial memory")
    
    client = NotionClient()
    collection = LazyDocumentCollection(client, preload_metadata=True)
    
    # Search by title (doesn't trigger content loading)
    start_time = time.time()
    title_results = collection.search_documents("meeting", search_titles=True, search_content=False)
    title_search_time = time.time() - start_time
    
    print(f"Found {len(title_results)} documents with 'meeting' in title in {title_search_time:.2f} seconds")
    for doc in title_results:
        print(f"- {doc.title}")
    print_memory_usage("After title search")
    
    # Search by content (triggers content loading only for searched documents)
    start_time = time.time()
    content_results = collection.search_documents("project", search_titles=False, search_content=True)
    content_search_time = time.time() - start_time
    
    print(f"Found {len(content_results)} documents with 'project' in content in {content_search_time:.2f} seconds")
    for doc in content_results:
        print(f"- {doc.title}")
    print_memory_usage("After content search")
    
    return {
        "title_search_time": title_search_time,
        "title_results": len(title_results),
        "content_search_time": content_search_time,
        "content_results": len(content_results)
    }


def batch_operations_example():
    """Demonstrate batch operations with lazy documents."""
    print("\n=== Batch Operations with Lazy Documents ===")
    print_memory_usage("Initial memory")
    
    client = NotionClient()
    collection = LazyDocumentCollection(client, preload_metadata=True)
    
    # Get a subset of document IDs
    document_ids = list(collection.documents.keys())[:10]  # First 10 documents
    
    # Batch preload documents
    start_time = time.time()
    collection.batch_preload(document_ids)
    preload_time = time.time() - start_time
    print(f"Batch preloaded {len(document_ids)} documents in {preload_time:.2f} seconds")
    print_memory_usage("After batch preload")
    
    # Process each document (should be faster now)
    processed_docs = 0
    start_time = time.time()
    for doc_id in document_ids:
        document = collection.documents[doc_id]
        if document._blocks_loaded:
            markdown = document.preview_text(n_chars=200)
            processed_docs += 1
    
    process_time = time.time() - start_time
    print(f"Processed {processed_docs} preloaded documents in {process_time:.2f} seconds")
    print_memory_usage("After processing")
    
    # Clear content
    collection.clear_loaded_content(keep_metadata=True)
    print_memory_usage("After clearing content")
    
    return {
        "preload_time": preload_time,
        "process_time": process_time,
        "document_count": processed_docs
    }


def compare_approaches():
    """Compare standard and lazy loading approaches."""
    print("\n=== Performance Comparison ===")
    
    # Run standard approach
    standard_results = standard_document_example()
    
    # Run lazy loading approach
    lazy_results = lazy_document_example()
    
    # Calculate memory efficiency
    process = psutil.Process()
    memory_info = process.memory_info()
    current_memory = memory_info.rss / (1024 * 1024)
    
    # Compare and print results
    print("\n=== Comparison Results ===")
    print(f"Documents processed: {standard_results['document_count']}")
    print(f"Standard approach:")
    print(f"  - List time: {standard_results['list_time']:.2f} seconds")
    print(f"  - Load time: {standard_results['load_time']:.2f} seconds")
    print(f"  - Process time: {standard_results['process_time']:.2f} seconds")
    print(f"  - Total time: {standard_results['list_time'] + standard_results['load_time'] + standard_results['process_time']:.2f} seconds")
    
    print(f"Lazy loading approach:")
    print(f"  - List time: {lazy_results['list_time']:.2f} seconds")
    print(f"  - Get time: {lazy_results['get_time']:.2f} seconds")
    print(f"  - Process time: {lazy_results['process_time']:.2f} seconds")
    print(f"  - Total time: {lazy_results['list_time'] + lazy_results['get_time'] + lazy_results['process_time']:.2f} seconds")
    
    # Compare search performance
    search_results = search_example()
    print(f"\nSearch performance:")
    print(f"  - Title search: {search_results['title_search_time']:.2f} seconds for {search_results['title_results']} results")
    print(f"  - Content search: {search_results['content_search_time']:.2f} seconds for {search_results['content_results']} results")
    
    # Compare batch operations
    batch_results = batch_operations_example()
    print(f"\nBatch operations:")
    print(f"  - Preload time: {batch_results['preload_time']:.2f} seconds for {batch_results['document_count']} documents")
    print(f"  - Process time: {batch_results['process_time']:.2f} seconds")
    
    print("\n=== Recommendations ===")
    print("1. Use LazyDocument for large documents to reduce memory usage")
    print("2. Use LazyDocumentCollection for managing multiple documents")
    print("3. Prefer title search over content search when possible for better performance")
    print("4. Use batch_preload for documents you know you'll need to process")
    print("5. Remember to clear content when finished to free memory")


if __name__ == "__main__":
    compare_approaches()