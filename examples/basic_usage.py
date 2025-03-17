"""
Example usage of the Notion NLP library with caching and rate limiting.
"""
from notionlp import NotionClient, TextProcessor, Hierarchy, Tagger, DEFAULT_CACHE_DIR
from notionlp.parsers import get_env
from notionlp.structure import AuthenticationError

def main():
    try:
        # Get token from environment variable
        notion_token = get_env('NOTION_API_TOKEN')
        if not notion_token:
            print("Error: NOTION_API_TOKEN environment variable not found")
            return

        # Initialize client with caching and rate limiting
        client = NotionClient(
            token=notion_token,
            cache_enabled=True,                 # Enable caching
            cache_dir=DEFAULT_CACHE_DIR,        # Use default cache directory
            max_cache_age_days=1,               # Cache valid for 1 day
            rate_limit=3                        # Limit to 3 requests per second (Notion API limit)
        )

        # Verify authentication
        if not client.authenticate():
            print("Authentication failed. Please check your token.")
            return

        # List available documents (uses cache if available)
        documents = client.list_documents()
        print(f"Found {len(documents)} documents")

        # Get content from first document
        if documents:
            doc = documents[0]
            print(f"\nProcessing document: {doc.title}")

            # The get_document_content method returns a tuple (metadata, blocks)
            metadata, blocks = client.get_document_content(doc.id)
            print(f"Retrieved {len(blocks)} blocks from document '{metadata.title}'")
            print(f"Last edited: {metadata.last_edited_time}")
            print(f"Last fetched: {metadata.last_fetched}")

            # Process text
            processor = TextProcessor()
            processed_blocks = processor.process_blocks(blocks)

            print("\nProcessed content:")
            for block in processed_blocks:
                print(f"- Found {len(block['entities'])} entities")
                print(f"- Keywords: {', '.join(block['keywords'])}")

            # Build hierarchy
            hierarchy = Hierarchy()
            root = hierarchy.build_hierarchy(blocks)

            print("\nDocument structure:")
            print(hierarchy.to_dict())

            # Generate tags
            tagger = Tagger()
            tagger.add_custom_tags(["important", "todo"])

            print("\nGenerated tags:")
            for block in blocks:
                tags = tagger.generate_tags(block)
                print(f"Block tags: {[tag.name for tag in tags]}")

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
