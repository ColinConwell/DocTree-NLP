"""
Example showing how to access raw Notion API data.

This example demonstrates how to use the get_all_available_data method
to retrieve and explore all available data from the Notion API for a document.
"""

import os
import json
from pathlib import Path
from pprint import pprint
from dotenv import load_dotenv

from doctree_nlp.api_client import NotionClient

# Load environment variables
load_dotenv()

# Get API token from environment variables
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")

# Initialize the client
client = NotionClient(token=NOTION_TOKEN)


def main():
    """Demonstrate raw Notion API data access."""
    print("Fetching documents from Notion...")
    documents = client.list_documents()

    if not documents:
        print("No documents found. Please ensure you have access to Notion documents.")
        return

    # Display available documents
    print("\nAvailable Documents:")
    for i, doc in enumerate(documents):
        print(f"{i+1}. {doc.title} ({doc.id})")

    # Ask user to select a document
    while True:
        try:
            choice = input(
                "\nSelect a document number (or press Enter for the first one): "
            )
            if not choice.strip():
                selected_index = 0
                break

            selected_index = int(choice) - 1
            if 0 <= selected_index < len(documents):
                break
            else:
                print(f"Please enter a number between 1 and {len(documents)}")
        except ValueError:
            print("Please enter a valid number")

    selected_doc = documents[selected_index]
    doc_id = selected_doc.id
    print(f"\nFetching all available data for document: {selected_doc.title}")

    try:
        # Get all available data from the Notion API
        raw_data = client.get_all_available_data(doc_id)

        # Check for API errors
        if "errors" in raw_data and raw_data["errors"]:
            print("\nSome errors occurred while fetching data:")
            for error_type, error_msg in raw_data["errors"].items():
                print(f"  • {error_type}: {error_msg}")

            if not raw_data["page_data"] and not raw_data["block_data"]:
                print("\nCritical errors prevented data retrieval. Exiting.")
                return

            print("\nContinuing with partial data...")

        # Demonstrate analyzing the data structure
        analyze_data_structure(raw_data)

        # Save the raw data to a file for further exploration
        output_path = Path("doctree_nlp_data") / "raw_data_example.json"
        save_raw_data(raw_data, output_path)

    except Exception as e:
        print(f"\nError retrieving document data: {str(e)}")


def analyze_data_structure(raw_data):
    """Analyze and display the structure of the raw Notion data."""
    print("\n== API DATA ANALYSIS ==")

    # Page data analysis
    if "page_data" in raw_data and raw_data["page_data"]:
        print("\n1. PAGE DATA:")
        page_data = raw_data["page_data"]

        # Page metadata
        print(f"  • Title: {extract_title(page_data)}")
        print(f"  • Created: {page_data.get('created_time', 'N/A')}")
        print(f"  • Last Edited: {page_data.get('last_edited_time', 'N/A')}")

        # Page properties
        if "properties" in page_data:
            print("\n  Page Properties:")
            for prop_name, prop_value in page_data["properties"].items():
                print(f"  • {prop_name}")

    # Block data analysis
    if "block_data" in raw_data and raw_data["block_data"]:
        blocks = raw_data["block_data"]
        print(f"\n2. CONTENT BLOCKS: {len(blocks)} blocks found")

        # Count block types
        block_types = {}
        for block in blocks:
            block_type = block.get("type", "unknown")
            block_types[block_type] = block_types.get(block_type, 0) + 1

        print("\n  Block Types:")
        for block_type, count in block_types.items():
            print(f"  • {block_type}: {count} blocks")

        # Sample first block of each type (for demonstration)
        print("\n  Sample First Block of Each Type:")
        shown_types = set()
        for block in blocks:
            block_type = block.get("type", "unknown")
            if (
                block_type not in shown_types and len(shown_types) < 5
            ):  # Limit to 5 examples
                shown_types.add(block_type)
                print(f"\n  • Type: {block_type}")
                if block_type in block:
                    block_content = block[block_type]
                    if "rich_text" in block_content:
                        text = extract_rich_text(block_content["rich_text"])
                        print(
                            f"    Content: {text[:50]}..."
                            if len(text) > 50
                            else f"    Content: {text}"
                        )

    # Other data sections
    if "comments_data" in raw_data and raw_data["comments_data"]:
        print(f"\n3. COMMENTS: {len(raw_data['comments_data'])} comments found")

    if "collection_data" in raw_data and raw_data["collection_data"]:
        print("\n4. DATABASE/COLLECTION DATA: Available")


def extract_title(page_data):
    """Extract the title from page data."""
    if "properties" not in page_data or "title" not in page_data["properties"]:
        return "Untitled"

    title_data = page_data["properties"]["title"]
    if isinstance(title_data, list):
        return "".join(
            part.get("text", {}).get("content", "")
            for part in title_data
            if isinstance(part, dict)
        )
    elif isinstance(title_data, dict) and "title" in title_data:
        return "".join(
            part.get("text", {}).get("content", "")
            for part in title_data["title"]
            if isinstance(part, dict)
        )

    return "Untitled"


def extract_rich_text(rich_text):
    """Extract text from rich_text array."""
    if not rich_text:
        return ""

    content = []
    for text in rich_text:
        if not isinstance(text, dict):
            continue

        # Try plain_text first, then fallback to text.content
        text_content = text.get("plain_text")
        if text_content is None:
            text_content = text.get("text", {}).get("content")

        if text_content:
            content.append(text_content)

    return "".join(content)


def save_raw_data(raw_data, output_path):
    """Save raw data to a file for further exploration."""
    # Ensure the output directory exists
    output_path.parent.mkdir(exist_ok=True, parents=True)

    # Save the data
    with open(output_path, "w") as f:
        json.dump(raw_data, f, indent=2)

    print(f"\nRaw data saved to {output_path} for further exploration")


if __name__ == "__main__":
    main()
