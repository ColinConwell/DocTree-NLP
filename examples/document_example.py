"""
Example showing the new Document class features.

This demonstrates how to work with Document objects to manipulate content,
build tree structures, and navigate document hierarchies.
"""
import os
from datetime import datetime
from doctree_nlp import NotionClient, Document, Block, Source

def main():
    """Run the document example."""
    
    print("=== Document Example ===")
    
    # Example 1: Create a document manually
    print("\n1. Creating a document manually:")
    manual_doc = Document(
        id="manual-doc",
        title="Manual Document",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        blocks=[
            Block(id="b1", type="heading_1", content="Introduction", has_children=False),
            Block(id="b2", type="paragraph", content="This is a sample document.", has_children=False),
            Block(id="b3", type="heading_2", content="Section 1", has_children=False),
            Block(id="b4", type="paragraph", content="Content in section 1.", has_children=False),
            Block(id="b5", type="heading_2", content="Section 2", has_children=False),
            Block(id="b6", type="paragraph", content="Content in section 2.", has_children=False),
            Block(id="b7", type="bulleted_list_item", content="List item 1", has_children=False),
            Block(id="b8", type="bulleted_list_item", content="List item 2", has_children=False),
        ]
    )
    
    # View document information
    print(f"Document: {manual_doc.title}")
    print(f"Created: {manual_doc.created_time}")
    print(f"Blocks: {len(manual_doc.blocks)}")
    
    # Preview the document
    print("\nText preview:")
    print(manual_doc.preview_text(n_chars=100))
    
    print("\nSentence preview:")
    print(manual_doc.preview_sentences(n=2))
    
    # Example 2: Build a document tree
    print("\n2. Building a document tree:")
    tree = manual_doc.build_tree()
    
    # Navigate the tree
    root = tree.root
    print(f"Root has {len(root.children)} children")
    
    # Find nodes by type
    headings = tree.find_nodes_by_type("heading_2")
    print(f"\nFound {len(headings)} h2 headings:")
    for heading in headings:
        print(f"- {heading.block.content}")
    
    # Find nodes by content
    content_nodes = tree.find_nodes_by_content("sample")
    print(f"\nFound {len(content_nodes)} nodes containing 'sample':")
    for node in content_nodes:
        print(f"- [{node.block.type}] {node.block.content}")
    
    # Example 3: Convert document to different formats
    print("\n3. Converting document to different formats:")
    
    # To markdown
    markdown = manual_doc.to_markdown()
    print("\nMarkdown:")
    print(markdown[:150] + "..." if len(markdown) > 150 else markdown)
    
    # To RST
    rst = manual_doc.to_rst()
    print("\nRST:")
    print(rst[:150] + "..." if len(rst) > 150 else rst)
    
    # To dictionary
    doc_dict = manual_doc.to_dict()
    print("\nDictionary (keys only):")
    print(list(doc_dict.keys()))
    
    # Example 4: Load from Notion (if token available)
    try:
        client = NotionClient(token="auto")
        
        print("\n4. Loading documents from Notion:")
        docs = client.list_documents()
        
        if docs:
            print(f"Found {len(docs)} documents")
            
            # Get first document with content
            document = client.get_document(docs[0].id)
            print(f"\nDocument: {document.title}")
            print(f"Blocks: {len(document.blocks)}")
            
            # Preview
            if document.blocks:
                print("\nPreview:")
                print(document.preview_text(n_chars=200))
                
                # Build tree
                document.build_tree()
                
                # Find headings
                headings = document.tree.find_nodes_by_type("heading_1")
                if headings:
                    print(f"\nHeadings: {len(headings)}")
                    for h in headings[:3]:  # Show first 3 only
                        print(f"- {h.block.content}")
        else:
            print("No documents found (check your Notion integration settings)")
    
    except Exception as e:
        print(f"\nSkipping Notion example: {str(e)}")
    
    # Example 5: Source class
    print("\n5. Creating a Source:")
    source = Source(
        id="source1",
        name="My Notion Workspace",
        api_type="notion",
        documents=["doc1", "doc2", "doc3"],
        metadata={
            "workspace_id": "workspace123",
            "user_count": 5,
            "created_date": "2023-01-15"
        }
    )
    
    print(f"Source: {source.name}")
    print(f"API Type: {source.api_type}")
    print(f"Documents: {len(source.documents)}")
    print(f"Metadata keys: {list(source.metadata.keys())}")
    
    # Add document
    source.add_document("doc4")
    print(f"Added document. New count: {len(source.documents)}")

if __name__ == "__main__":
    main()