"""
Example demonstrating the auto token discovery feature.
"""
from notionlp import NotionClient

def main():
    """
    Demonstrate auto token discovery in NotionClient.
    
    This example will:
    1. Create a NotionClient with auto token discovery
    2. Search for a token in environment variables, .env files, and user input
    3. Once authenticated, list available documents
    """
    print("Initializing NotionClient with auto token discovery...")
    
    try:
        # Initialize with auto token discovery
        client = NotionClient(token="auto")
        print("✓ Successfully authenticated with auto-discovered token!")
        
        # Test the client by listing documents
        print("\nFetching documents to verify authentication...")
        documents = client.list_documents()
        
        if documents:
            print(f"✓ Authentication successful! Found {len(documents)} documents:")
            for i, doc in enumerate(documents[:5]):  # Show first 5 docs
                print(f"  {i+1}. {doc.title}")
            
            if len(documents) > 5:
                print(f"  ... and {len(documents) - 5} more")
        else:
            print("✓ Authentication successful! No documents found or accessible.")
            print("  Make sure you've shared documents with your integration.")
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Create a .env file with your token: echo 'NOTION_API_TOKEN=your-token' > .env")
        print("2. Or set an environment variable: export NOTION_API_TOKEN=your-token")
        print("3. Make sure your token is valid and has appropriate permissions")
        print("4. Ensure you've shared your Notion pages with the integration")

if __name__ == "__main__":
    main()