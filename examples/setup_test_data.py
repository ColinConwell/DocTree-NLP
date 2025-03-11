"""
Helper script to create test data in Notion for testing the Notion NLP library.
"""
import os
from notion_nlp import NotionClient
from notion_nlp.exceptions import NotionNLPError

def find_parent_page(client: NotionClient) -> str:
    """Find a suitable parent page for our test document."""
    try:
        # Search for pages we have access to
        response = client._post("search", json={
            "filter": {
                "property": "object",
                "value": "page"
            }
        })

        if response.status_code != 200:
            raise NotionNLPError(f"Failed to search for parent pages: {response.text}")

        results = response.json().get("results", [])
        if not results:
            raise NotionNLPError("No accessible pages found. Please ensure you have access to at least one page in your Notion workspace.")

        # Use the first available page as parent
        return results[0]["id"]

    except Exception as e:
        raise NotionNLPError(f"Error finding parent page: {str(e)}")

def create_test_page(client: NotionClient) -> str:
    """Create a test page with sufficient content for testing."""
    try:
        # First find a parent page
        parent_id = find_parent_page(client)

        # Create a new page with test content
        page_data = {
            "parent": {"type": "page_id", "page_id": parent_id},
            "properties": {
                "title": [{"text": {"content": "Notion NLP Test Document"}}]
            },
            "children": [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": "Testing Document Structure"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": "This is a test document created for the Notion NLP library testing purposes."}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Sample Content Section"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": "John works at Apple Inc. in California. The company is known for its innovative technology products."}}]
                    }
                }
            ]
        }

        response = client._post("pages", json=page_data)
        if response.status_code == 200:
            return response.json()["id"]
        else:
            raise NotionNLPError(f"Failed to create test page: {response.text}")

    except Exception as e:
        raise NotionNLPError(f"Error creating test data: {str(e)}")

def main():
    """Main function to set up test data."""
    try:
        notion_token = os.environ.get('NOTION_API_TOKEN')
        if not notion_token:
            raise NotionNLPError("NOTION_API_TOKEN not found in environment variables")

        print("Initializing Notion client...")
        client = NotionClient(notion_token)

        print("\nCreating test document...")
        page_id = create_test_page(client)
        print(f"Test document created successfully! Page ID: {page_id}")
        print("\nYou can now run the test_functionality.py script to test the library.")

    except NotionNLPError as e:
        print(f"Setup error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()