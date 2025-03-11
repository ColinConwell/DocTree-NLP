"""
Test script to verify core functionality of the Notion NLP library.
"""
import os
from typing import List, Dict
from notion_nlp import (
    NotionClient, 
    TextProcessor, 
    Hierarchy, 
    Tagger,
    Document,
    Block
)
from notion_nlp.core import NotionNLPError

def analyze_document_structure(blocks: List[Block]):
    """Analyze and display document structure."""
    hierarchy = Hierarchy()
    root = hierarchy.build_hierarchy(blocks)

    # Convert to JSON for pretty printing
    structure = hierarchy.to_dict()
    print("\nDocument Structure:")
    for block in blocks:
        print(f"- {block.type}: {block.content[:50]}...")

    return structure

def perform_nlp_analysis(processor: TextProcessor, tagger: Tagger, blocks: List[Block]):
    """Perform NLP analysis on document content."""
    print("\nNLP Analysis:")

    # Process blocks
    processed_blocks = processor.process_blocks(blocks)

    for idx, block in enumerate(processed_blocks):
        print(f"\nBlock {idx + 1}:")
        print(f"Content: {block['content'][:100]}...")

        # Display entities
        print("Named Entities:")
        for entity in block['entities']:
            print(f"- {entity['text']} ({entity['label']})")

        # Display keywords
        print("Keywords:", ", ".join(block['keywords']))

        # Generate tags
        tags = tagger.generate_tags(blocks[idx])
        print("Generated Tags:", ", ".join(tag.name for tag in tags))

        # Analyze sentiment
        sentiment = tagger.analyze_sentiment(block['content'])
        print(f"Sentiment: {sentiment}")

        # Generate summary if content is long enough
        if len(block['content'].split()) > 30:
            summary = processor.extract_summary(block['content'], sentences=2)
            print(f"Summary: {summary}")

def main():
    """Main test function."""
    try:
        # Initialize clients
        notion_token = os.environ.get('NOTION_API_TOKEN')
        if not notion_token:
            raise NotionNLPError("NOTION_API_TOKEN not found in environment variables")

        print("Initializing clients...")
        client = NotionClient(notion_token)
        processor = TextProcessor()
        tagger = Tagger()

        # Add some custom tags for testing
        tagger.add_custom_tags(["important", "review", "followup"])

        # List available documents
        print("\nFetching available documents...")
        documents = client.list_documents()
        print(f"Found {len(documents)} documents")

        if not documents:
            print("No documents available for analysis")
            return

        # Select the first document for analysis
        doc = documents[0]
        print(f"\nAnalyzing document: {doc.title}")

        # Get document content
        blocks = client.get_document_content(doc.id)
        print(f"Retrieved {len(blocks)} blocks of content")

        # Analyze document structure
        print("\nAnalyzing document structure...")
        structure = analyze_document_structure(blocks)

        # Perform NLP analysis
        print("\nPerforming NLP analysis...")
        perform_nlp_analysis(processor, tagger, blocks)

        print("\nTest completed successfully!")

    except NotionNLPError as e:
        print(f"Notion NLP Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()