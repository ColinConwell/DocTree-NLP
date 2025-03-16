#!/usr/bin/env python3
"""
Script to fix the Jupyter notebook and make it runnable.
"""
import json
import nbformat

# Define a valid notebook structure
notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "# NotioNLPToolkit Demo\n\nThis notebook demonstrates the core functionalities of the Notion NLP library, including:\n- Authentication with Notion API\n- Listing and accessing documents\n- Processing text with NLP capabilities\n- Building document hierarchies\n- Automatic tagging\n\nFirst, let's import the required modules:"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "import os\nfrom notionlp import (\n    NotionClient,\n    Hierarchy,\n    Tagger,\n    TextProcessor,\n    DEFAULT_CACHE_DIR\n)"
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "## 1. Authentication\n\nFirst, we'll initialize the Notion client with our API token:"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# Get token from environment variable\nnotion_token = os.environ.get('NOTION_API_TOKEN')\n\n# Initialize client with caching and rate limiting\nclient = NotionClient(\n    token=notion_token,\n    cache_enabled=True,                 # Enable caching for faster repeat queries\n    cache_dir=DEFAULT_CACHE_DIR,        # Use default cache directory\n    max_cache_age_days=1,               # Cache valid for 1 day\n    rate_limit=3                        # Limit to 3 requests per second (Notion API limit)\n)\n\n# Verify authentication\nauth_status = client.authenticate()\nprint(f\"Authentication status: {'Successful' if auth_status else 'Failed'}\")\n\n# Display cache information\ntry:\n    cache_info = client.get_cache_info()\n    print(f\"\\nCache configuration:\")\n    print(f\"- Cache enabled: {cache_info['enabled']}\")\n    print(f\"- Cache directory: {cache_info['cache_dir']}\")\n    print(f\"- Max age: {cache_info['max_age_days']} days\")\nexcept Exception as e:\n    print(f\"Could not get cache info: {e}\")"
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "## 2. Listing Documents\n\nLet's retrieve and display the list of available documents:"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "# List documents (uses cache if available)\nprint(\"Fetching documents (will use cache after first run)...\")\ndocuments = client.list_documents()\nprint(f\"Found {len(documents)} documents:\")\nfor doc in documents:\n    print(f\"- {doc.title} (ID: {doc.id})\")\n    print(f\"  Last edited: {doc.last_edited_time}\")"
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "## 3. Processing Document Content\n\nNow, let's fetch and process the content of the first document:"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "if documents:\n    # Get document content\n    doc = documents[0]\n    print(f\"Processing document: {doc.title}\")\n    \n    # Note: get_document_content now returns a tuple (document, blocks)\n    document, blocks = client.get_document_content(doc.id)\n    print(f\"Retrieved {len(blocks)} blocks from document\")\n    print(f\"Document last edited: {document.last_edited_time}\")\n    print(f\"Last fetched from API: {document.last_fetched}\")\n    \n    # Process text\n    processor = TextProcessor()\n    processed_blocks = processor.process_blocks(blocks)\n    \n    # Display results\n    print(\"\\nProcessed content:\")\n    for block in processed_blocks[:2]:  # Show first 2 blocks for brevity\n        print(f\"\\nBlock type: {block['type']}\")\n        print(f\"Entities found: {[e['text'] for e in block['entities']]}\")\n        print(f\"Keywords: {block['keywords']}\")\n    \n    # Try forcing a refresh (bypassing cache)\n    print(\"\\nForcing refresh (bypassing cache):\")\n    document, blocks = client.get_document_content(doc.id, use_cache=False)\n    print(f\"Retrieved {len(blocks)} blocks directly from API\")"
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "## 4. Building Document Hierarchy\n\nLet's analyze the document's structure:"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "if documents:\n    # Build hierarchy\n    hierarchy = Hierarchy()\n    root = hierarchy.build_hierarchy(blocks)\n    \n    # Convert to dictionary for visualization\n    structure = hierarchy.to_dict()\n    print(\"Document structure:\")\n    print(structure)\n    \n    # Check cache status after operations\n    try:\n        cache_info = client.get_cache_info()\n        print(f\"\\nCache status after operations:\")\n        print(f\"- Files in cache: {cache_info['num_files']}\")\n        print(f\"- Cache size: {cache_info['total_size_mb']:.2f} MB\")\n    except Exception as e:\n        print(f\"Could not get cache info: {e}\")"
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": "## 5. Automatic Tagging\n\nFinally, let's generate tags for the document content:"
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "if documents:\n    # Initialize tagger\n    tagger = Tagger()\n    \n    # Add some custom tags\n    tagger.add_custom_tags([\"important\", \"review\", \"followup\"])\n    \n    print(\"Generated tags:\")\n    for block in blocks[:3]:  # Process first 3 blocks for demonstration\n        tags = tagger.generate_tags(block)\n        print(f\"\\nBlock content: {block.content[:50]}...\")\n        print(f\"Tags: {[tag.name for tag in tags]}\")\n        \n        # Analyze sentiment\n        sentiment = tagger.analyze_sentiment(block.content)\n        print(f\"Sentiment: {sentiment}\")"
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {
                "name": "ipython",
                "version": 3
            },
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.11"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Write the fixed notebook
with open('/Users/colinconwell/GitHub/NotioNLPToolkit/demo/main_demo.ipynb', 'w') as f:
    json.dump(notebook, f, indent=1)

print("Notebook has been fixed!")