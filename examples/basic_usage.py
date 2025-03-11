"""
Example usage of the Notion NLP library.
"""
from notion_nlp import NotionClient, TextProcessor, Hierarchy, Tagger
from notion_nlp.env_loader import get_env
from notion_nlp.exceptions import AuthenticationError

def main():
    try:
        # Get token from environment variable
        notion_token = get_env('NOTION_API_TOKEN')
        if not notion_token:
            print("Error: NOTION_API_TOKEN environment variable not found")
            return

        client = NotionClient(notion_token)

        # Verify authentication
        if not client.authenticate():
            print("Authentication failed. Please check your token.")
            return

        # List available documents
        documents = client.list_documents()
        print(f"Found {len(documents)} documents")

        # Get content from first document
        if documents:
            doc = documents[0]
            print(f"\nProcessing document: {doc.title}")

            blocks = client.get_document_content(doc.id)

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

    except AuthenticationError as e:
        print(f"Authentication error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
