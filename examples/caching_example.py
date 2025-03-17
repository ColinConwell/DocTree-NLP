"""
Example demonstrating the caching and rate limiting features of the Notion client.
"""
import os
import time
from dotenv import load_dotenv
from notionlp import NotionClient, DEFAULT_CACHE_DIR

# Load environment variables
load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

def main():
    # Create standard client with default caching
    client = NotionClient(
        token=NOTION_API_KEY,
        cache_enabled=True,
        cache_dir=DEFAULT_CACHE_DIR,
        max_cache_age_days=1,  # Cache valid for 1 day
        rate_limit=3  # 3 requests per second
    )
    
    # Authenticate
    if not client.authenticate():
        print("Authentication failed")
        return
    
    print("\n===== First Run (No Cache) =====")
    start_time = time.time()
    
    # List documents (this will build the cache)
    print("Fetching document list...")
    documents = client.list_documents()
    print(f"Found {len(documents)} documents")
    
    # Get the first document (this will also be cached)
    if documents:
        doc = documents[0]
        print(f"Fetching document '{doc.title}'...")
        metadata, blocks = client.get_document_content(doc.id)
        print(f"Retrieved {len(blocks)} blocks from document '{metadata.title}'")
    
    end_time = time.time()
    print(f"First run took {end_time - start_time:.2f} seconds")
    
    # Display cache info
    cache_info = client.get_cache_info()
    print("\n===== Cache Information =====")
    print(f"Cache enabled: {cache_info['enabled']}")
    print(f"Cache directory: {cache_info['cache_dir']}")
    print(f"Max age: {cache_info['max_age_days']} days")
    print(f"Files: {cache_info['num_files']}")
    print(f"Size: {cache_info['total_size_mb']:.2f} MB")
    
    # Second run (using cache)
    print("\n===== Second Run (Using Cache) =====")
    start_time = time.time()
    
    # List documents (should use cache)
    print("Fetching document list...")
    documents = client.list_documents()
    print(f"Found {len(documents)} documents")
    
    # Get the first document (should use cache)
    if documents:
        doc = documents[0]
        print(f"Fetching document '{doc.title}'...")
        metadata, blocks = client.get_document_content(doc.id)
        print(f"Retrieved {len(blocks)} blocks from document '{metadata.title}'")
    
    end_time = time.time()
    print(f"Second run took {end_time - start_time:.2f} seconds")
    
    # Disable cache for specific request
    if documents:
        print("\n===== Force Bypass Cache =====")
        start_time = time.time()
        doc = documents[0]
        print(f"Fetching document '{doc.title}' without cache...")
        metadata, blocks = client.get_document_content(doc.id, use_cache=False)
        end_time = time.time()
        print(f"Retrieved {len(blocks)} blocks from document '{metadata.title}'")
        print(f"Force fetching took {end_time - start_time:.2f} seconds")
    
    # Clear specific document from cache
    if documents:
        doc = documents[0]
        print(f"\nClearing cache for document '{doc.title}'...")
        client.clear_document_cache(doc.id)
        
        # Get cache info after clearing
        cache_info = client.get_cache_info()
        print(f"Files after clearing: {cache_info['num_files']}")
    
    # Clear all cache
    print("\nClearing all cache...")
    client.clear_cache()
    
    # Get cache info after clearing all
    cache_info = client.get_cache_info()
    print(f"Files after clearing all: {cache_info['num_files']}")

if __name__ == "__main__":
    main()