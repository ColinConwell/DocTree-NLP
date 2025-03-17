"""
Simple script to check Notion API access and list available documents.
Demonstrates the use of caching and rate limiting features.
"""
import os
import time
from notionlp.api_client import (
    NotionClient, AuthenticationError, NotionNLPError, CacheError
)
from notionlp.cache_manager import DEFAULT_CACHE_DIR

def main():
    try:
        # Get token from environment
        notion_token = os.environ.get('NOTION_API_TOKEN')
        if not notion_token:
            print("Error: NOTION_API_TOKEN environment variable not found")
            return

        # Initialize client with caching and rate limiting
        print("Initializing Notion client with caching and rate limiting...")
        client = NotionClient(
            token=notion_token,
            cache_enabled=True,                 # Enable caching
            cache_dir=DEFAULT_CACHE_DIR,        # Use default cache directory
            max_cache_age_days=1,               # Cache valid for 1 day
            rate_limit=3                        # Limit to 3 requests per second (Notion API limit)
        )

        # Verify authentication
        print("\nVerifying authentication...")
        if client.authenticate():
            print("✓ Authentication successful")
        else:
            print("✗ Authentication failed")
            return

        # First API call - no cache
        print("\n===== First Run (No Cache) =====")
        start_time = time.time()
        
        # List documents
        print("Fetching available documents...")
        documents = client.list_documents()
        print(f"Found {len(documents)} documents:")
        
        # Get cache info
        try:
            cache_info = client.get_cache_info()
            print(f"\nCache status: {cache_info['num_files']} files, {cache_info['total_size_mb']:.2f} MB")
        except CacheError as e:
            print(f"Cache error: {str(e)}")
            
        first_run_time = time.time() - start_time
        print(f"First run took {first_run_time:.2f} seconds")
        
        # Second API call - should use cache
        print("\n===== Second Run (Using Cache) =====")
        start_time = time.time()
        
        # List documents (should use cache)
        print("Fetching available documents (from cache)...")
        documents = client.list_documents()
        print(f"Found {len(documents)} documents:")
        
        second_run_time = time.time() - start_time
        print(f"Second run took {second_run_time:.2f} seconds")
        print(f"Speedup: {first_run_time / second_run_time:.1f}x faster with cache")
        
        # Process each document
        for doc in documents:
            print(f"\nDocument:")
            print(f"  Title: {doc.title}")
            print(f"  ID: {doc.id}")
            print(f"  Created: {doc.created_time}")
            print(f"  Last edited: {doc.last_edited_time}")
            
            # Try to fetch content
            print("\nFetching document content...")
            try:
                # Note: get_document_content returns tuple (metadata, blocks)
                metadata, blocks = client.get_document_content(doc.id)
                print(f"✓ Successfully retrieved {len(blocks)} blocks")
                print(f"  Last fetched: {metadata.last_fetched}")
                
                # Display first few blocks
                for i, block in enumerate(blocks[:3]):
                    print(f"\nBlock {i+1}:")
                    print(f"  Type: {block.type}")
                    print(f"  Content: {block.content[:100]}...")
                
                # Force refresh without cache
                print("\nForcing fresh fetch (bypassing cache)...")
                start_time = time.time()
                metadata, blocks = client.get_document_content(doc.id, use_cache=False)
                print(f"✓ Successfully retrieved {len(blocks)} blocks in {time.time() - start_time:.2f} seconds")
                    
            except NotionNLPError as e:
                print(f"✗ Error fetching content: {str(e)}")

    except AuthenticationError as e:
        print(f"Authentication error: {str(e)}")
    except CacheError as e:
        print(f"Cache error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
