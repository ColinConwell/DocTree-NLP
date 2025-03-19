"""
Example showing Source class features.

This demonstrates how to work with Source objects to manage collections
of documents and associated metadata.
"""
import os
from datetime import datetime
from doctree_nlp import Source, Document, Block

def main():
    """Run the Source example."""
    
    print("=== Source Example ===")
    
    # Example 1: Create a source manually
    print("\n1. Creating a source manually:")
    source = Source(
        id="src1",
        name="Research Project Documents",
        api_type="notion",
        documents=["doc1", "doc2", "doc3"],
        metadata={
            "workspace_id": "workspace123",
            "owner": "jane.doe@example.com",
            "team_size": 5,
            "project_start": "2023-01-15",
            "tags": ["research", "documentation", "analysis"]
        },
        last_synced=datetime.now()
    )
    
    # View source information
    print(f"Source: {source.name}")
    print(f"API Type: {source.api_type}")
    print(f"Documents: {len(source.documents)}")
    print(f"Last synced: {source.last_synced}")
    
    # Example 2: Add documents to source
    print("\n2. Adding documents to source:")
    source.add_document("doc4")
    source.add_document("doc5")
    print(f"Documents after adding: {len(source.documents)}")
    
    # Try adding a duplicate document (should not increase count)
    source.add_document("doc3")
    print(f"Documents after adding duplicate: {len(source.documents)}")
    
    # Example 3: Create a collection of documents
    print("\n3. Creating document collection:")
    
    # Create sample documents
    docs = [
        Document(
            id="doc1",
            title="Research Proposal",
            created_time=datetime(2023, 1, 15, 9, 0, 0),
            last_edited_time=datetime(2023, 1, 20, 14, 30, 0),
            source_id="src1",
            blocks=[
                Block(id="b1", type="heading_1", content="Research Proposal", has_children=False),
                Block(id="b2", type="paragraph", content="Project overview and goals.", has_children=False),
            ]
        ),
        Document(
            id="doc2",
            title="Literature Review",
            created_time=datetime(2023, 2, 5, 10, 0, 0),
            last_edited_time=datetime(2023, 2, 10, 16, 45, 0),
            source_id="src1",
            blocks=[
                Block(id="b3", type="heading_1", content="Literature Review", has_children=False),
                Block(id="b4", type="paragraph", content="Summary of existing research.", has_children=False),
            ]
        ),
        Document(
            id="doc3",
            title="Methodology",
            created_time=datetime(2023, 3, 12, 11, 30, 0),
            last_edited_time=datetime(2023, 3, 15, 9, 15, 0),
            source_id="src1",
            blocks=[
                Block(id="b5", type="heading_1", content="Methodology", has_children=False),
                Block(id="b6", type="paragraph", content="Research approach and methods.", has_children=False),
            ]
        )
    ]
    
    # Print document collection
    print(f"Collection contains {len(docs)} documents:")
    for doc in docs:
        print(f"- {doc.title} (Created: {doc.created_time.strftime('%Y-%m-%d')})")
    
    # Example 4: Use pandas DataFrame integration (if available)
    print("\n4. Creating DataFrame from source metadata:")
    try:
        df = source.to_dataframe()
        if df is not None:
            print(f"DataFrame created with shape: {df.shape}")
            print("\nColumns:", ", ".join(df.columns))
            print("\nFirst few rows:")
            print(df.head())
        else:
            print("DataFrame creation returned None (pandas may not be installed)")
    except Exception as e:
        print(f"Could not create DataFrame: {str(e)}")
    
    # Example 5: Source with structured document retrieval
    print("\n5. Source with document retrieval:")
    
    # In a real application, you would have a function to retrieve documents
    # by their IDs from the source. Here's a simplified example:
    
    def get_document_by_id(doc_id, doc_list):
        """Simulate document retrieval by ID."""
        for doc in doc_list:
            if doc.id == doc_id:
                return doc
        return None
    
    # List the documents in the source
    print(f"Source contains {len(source.documents)} document IDs:")
    for i, doc_id in enumerate(source.documents[:3]):  # Show first 3
        print(f"{i+1}. {doc_id}")
    
    # Retrieve a document
    if source.documents:
        doc_id_to_fetch = source.documents[0]
        print(f"\nFetching document with ID: {doc_id_to_fetch}")
        
        doc = get_document_by_id(doc_id_to_fetch, docs)
        if doc:
            print(f"Found: {doc.title}")
            print(f"Created: {doc.created_time}")
            print(f"Blocks: {len(doc.blocks)}")
        else:
            print(f"Document {doc_id_to_fetch} not found in collection")

if __name__ == "__main__":
    main()