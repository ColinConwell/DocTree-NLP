"""
Example showing Jupyter notebook integration features.

This demonstrates how to use the notebook display functions
for rich Document visualization in Jupyter notebooks.

Note: This script should be run in a Jupyter notebook environment.
"""

# This example should be run in a Jupyter notebook
# We'll check if we're in a notebook environment

def is_notebook():
    """Check if running in a notebook environment."""
    try:
        from IPython import get_ipython
        if get_ipython() is None:
            return False
        if 'IPKernelApp' not in get_ipython().config:
            return False
        return True
    except ImportError:
        return False

def main():
    """Run the Jupyter notebook example."""
    
    # Only proceed if in a notebook
    if not is_notebook():
        print("""
        This example is designed to be run in a Jupyter notebook. 
        Please open this file in a notebook and run it there.
        
        In your notebook, you can use:
        
        ```python
        from notionlp import NotionClient, display_document, display_document_tree, display_document_table
        
        # Initialize client and get document
        client = NotionClient(token="auto")
        document = client.get_document("your-document-id")
        
        # Display document in different formats
        display_document(document)
        display_document_tree(document)
        display_document_table(document)
        ```
        """)
        return
    
    # Import necessary modules
    from datetime import datetime
    from notionlp import Document, Block
    from notionlp.notebook import (
        display_document, 
        display_document_tree, 
        display_document_table
    )
    
    # Create a sample document
    document = Document(
        id="sample-doc",
        title="Sample Document for Notebook Display",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        blocks=[
            Block(id="b1", type="heading_1", content="Introduction", has_children=False),
            Block(id="b2", type="paragraph", content="This is a sample document for testing Jupyter notebook display features.", has_children=False),
            Block(id="b3", type="heading_2", content="Section 1", has_children=False),
            Block(id="b4", type="paragraph", content="This section demonstrates the structure of the document.", has_children=False),
            Block(id="b5", type="bulleted_list_item", content="List item 1", has_children=False),
            Block(id="b6", type="bulleted_list_item", content="List item 2", has_children=False),
            Block(id="b7", type="heading_2", content="Section 2", has_children=False),
            Block(id="b8", type="paragraph", content="This section shows more content types.", has_children=False),
            Block(id="b9", type="numbered_list_item", content="First item", has_children=False),
            Block(id="b10", type="numbered_list_item", content="Second item", has_children=False),
            Block(id="b11", type="quote", content="This is a quote block", has_children=False),
            Block(id="b12", type="code", content="print('Hello, world!')", has_children=False),
        ]
    )
    
    # Build the document tree
    document.build_tree()
    
    # Display normal document view
    print("Document display:")
    display_document(document)
    
    # Display document tree view (interactive)
    print("\nDocument tree view:")
    display_document_tree(document)
    
    # Display document table view
    print("\nDocument table view:")
    display_document_table(document)
    
    # Display automatic tree building
    doc_without_tree = Document(
        id="no-tree-doc",
        title="Document without pre-built tree",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        blocks=[
            Block(id="c1", type="heading_1", content="Auto-build test", has_children=False),
            Block(id="c2", type="paragraph", content="This document will have its tree auto-built.", has_children=False),
        ]
    )
    
    print("\nDocument with auto-built tree:")
    display_document_tree(doc_without_tree)  # Tree will be built automatically
    
    # Try loading from Notion if available
    try:
        from notionlp import NotionClient
        
        client = NotionClient(token="auto")
        documents = client.list_documents()
        
        if documents:
            print("\nShowing a real Notion document:")
            doc = client.get_document(documents[0].id)
            display_document(doc)
            display_document_table(doc)
            display_document_tree(doc)
    except Exception as e:
        print(f"Couldn't load Notion document: {str(e)}")

if __name__ == "__main__":
    main()