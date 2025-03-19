"""
Example usage of the DocTree NLP library with caching and rate limiting.
"""
from doctree_nlp import (
    NotionClient, 
    TextProcessor, 
    Tagger, 
    Document, 
)
from doctree_nlp.defaults import get_default
from doctree_nlp.env_loader import get_env
from doctree_nlp.api_client import AuthenticationError

def main():
    try:
        # Using auto token discovery (recommended approach)
        client = NotionClient(
            token="auto",                      # Auto-discover token
            cache_enabled=True,                # Enable caching
            cache_dir=get_default('cache.directory'),  # Use default cache directory
            max_cache_age_days=1,              # Cache valid for 1 day
            rate_limit=3                       # Limit to 3 requests per second (Notion API limit)
        )
        
        # Alternative approach using get_env for demonstration:
        # notion_token = get_env('NOTION_API_TOKEN')
        # if not notion_token:
        #     print("Error: NOTION_API_TOKEN environment variable not found")
        #     return
        # client = NotionClient(token=notion_token, ...)

        # Verify authentication
        if not client.authenticate():
            print("Authentication failed. Please check your token.")
            return

        # List available documents (uses cache if available)
        documents = client.list_documents()
        print(f"Found {len(documents)} documents")

        # Get content from first document
        if documents:
            doc_id = documents[0].id
            print(f"\nProcessing document: {documents[0].title}")

            # Get document content and create a Document instance
            document = client.get_document(doc_id)
            
            # Build document tree
            document.build_tree()
            
            print(f"Retrieved {len(document.blocks)} blocks from document '{document.title}'")
            print(f"Last edited: {document.last_edited_time}")
            print(f"Last fetched: {document.last_fetched}")

            # Process text
            processor = TextProcessor()
            processed_blocks = processor.process_blocks(document.blocks)

            print("\nProcessed content:")
            for block in processed_blocks:
                print(f"- Found {len(block['entities'])} entities")
                print(f"- Keywords: {', '.join(block['keywords'])}")

            # Show document preview
            print("\nDocument preview:")
            print(document.preview_text(n_chars=200))
            
            # Convert to different formats
            print("\nMarkdown preview:")
            markdown = document.to_markdown()
            print(markdown[:200] + "..." if len(markdown) > 200 else markdown)
            
            # Document structure
            print("\nDocument structure:")
            print(f"Tree depth: {len(document.tree.find_nodes_by_type('heading_1'))}")
            
            # Generate tags
            tagger = Tagger()
            tagger.add_custom_tags(["important", "todo"])

            print("\nGenerated tags:")
            doc_tags = tagger.tag_document(document)
            tag_count = sum(len(tags) for tags in doc_tags.values())
            print(f"Generated {tag_count} tags across {len(doc_tags)} blocks")

            # Display cache information
            try:
                cache_info = client.get_cache_info()
                print("\nCache Information:")
                print(f"Cache enabled: {cache_info['enabled']}")
                print(f"Cache directory: {cache_info['cache_dir']}")
                print(f"Cache size: {cache_info['total_size_mb']:.2f} MB")
                print(f"Number of cached files: {cache_info['num_files']}")
            except Exception as e:
                print(f"Error getting cache info: {e}")

    except AuthenticationError as e:
        print(f"Authentication error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
