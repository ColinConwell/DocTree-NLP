"""
Simple script to check Notion API access and list available documents.
"""
import os
from notion_nlp import NotionClient
from notion_nlp.core import AuthenticationError, NotionNLPError

def main():
    try:
        # Get token from environment
        notion_token = os.environ.get('NOTION_API_TOKEN')
        if not notion_token:
            print("Error: NOTION_API_TOKEN environment variable not found")
            return

        # Initialize client
        print("Initializing Notion client...")
        client = NotionClient(notion_token)

        # Verify authentication
        print("\nVerifying authentication...")
        if client.authenticate():
            print("✓ Authentication successful")
        else:
            print("✗ Authentication failed")
            return

        # List documents
        print("\nFetching available documents...")
        documents = client.list_documents()
        print(f"Found {len(documents)} documents:")
        
        for doc in documents:
            print(f"\nDocument:")
            print(f"  Title: {doc.title}")
            print(f"  ID: {doc.id}")
            print(f"  Created: {doc.created_time}")
            print(f"  Last edited: {doc.last_edited_time}")
            
            # Try to fetch content
            print("\nFetching document content...")
            try:
                blocks = client.get_document_content(doc.id)
                print(f"✓ Successfully retrieved {len(blocks)} blocks")
                
                # Display first few blocks
                for i, block in enumerate(blocks[:3]):
                    print(f"\nBlock {i+1}:")
                    print(f"  Type: {block.type}")
                    print(f"  Content: {block.content[:100]}...")
                    
            except NotionNLPError as e:
                print(f"✗ Error fetching content: {str(e)}")

    except AuthenticationError as e:
        print(f"Authentication error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
