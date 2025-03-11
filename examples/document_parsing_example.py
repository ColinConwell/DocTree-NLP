"""
Example script demonstrating the document parsing functionality of NotioNLPToolkit.

This script shows how to:
1. Load example documents
2. Convert documents to different formats (dict, markdown, RST)
3. Work with the document hierarchy
"""
import json
import os
from pathlib import Path

from notion_nlp import (
    Block, 
    Hierarchy, 
    TextProcessor, 
    Tagger
)
from notion_nlp.parsers import (
    doc_to_dict, 
    export_to_markdown, 
    export_to_rst, 
    load_example_document
)

def print_separator(title):
    """Print a section separator with title."""
    print("\n" + "=" * 70)
    print(f" {title} ".center(70, "="))
    print("=" * 70 + "\n")


def main():
    """Run the document parsing examples."""
    # Example 1: Load a sample document and convert to dictionary
    print_separator("Loading Example Document")
    meeting_blocks = load_example_document("meeting_notes")
    print(f"Loaded {len(meeting_blocks)} blocks from meeting_notes.json")
    
    # Create a hierarchy from the blocks
    meeting_hierarchy = Hierarchy()
    meeting_hierarchy.build_hierarchy(meeting_blocks)
    print(f"Created hierarchy with root node and {len(meeting_hierarchy.root.children)} top-level children")
    
    # Convert to dictionary
    print_separator("Document as Dictionary")
    meeting_dict = doc_to_dict(meeting_hierarchy)
    print(json.dumps(meeting_dict, indent=2)[:1000] + "...\n")  # Show first 1000 chars
    
    # Convert to markdown
    print_separator("Document as Markdown")
    meeting_md = export_to_markdown(meeting_hierarchy)
    print(meeting_md[:1000] + "...\n")  # Show first 1000 chars
    
    # Save the markdown to a file
    md_path = Path(__file__).parent / "output" / "meeting_notes.md"
    os.makedirs(md_path.parent, exist_ok=True)
    with open(md_path, "w") as f:
        f.write(meeting_md)
    print(f"Saved full markdown to {md_path}")
    
    # Example 2: Load another document and convert to RST
    print_separator("Working with Another Document")
    product_blocks = load_example_document("product_specs")
    product_hierarchy = Hierarchy()
    product_hierarchy.build_hierarchy(product_blocks)
    
    # For simplicity, let's skip the NLP processing for now 
    # and directly use the original blocks
    print("Skipping NLP processing for simplicity...")
    
    # Convert to RST
    print_separator("Document as RST")
    product_rst = export_to_rst(product_blocks)
    print(product_rst[:1000] + "...\n")  # Show first 1000 chars
    
    # Save RST to file
    rst_path = Path(__file__).parent / "output" / "product_specs.rst"
    with open(rst_path, "w") as f:
        f.write(product_rst)
    print(f"Saved full RST to {rst_path}")
    
    # Example 3: Working with the document hierarchy
    print_separator("Hierarchy Operations")
    # Find all heading blocks
    heading_blocks = [b for b in meeting_blocks if b.type.startswith("heading_")]
    print(f"Found {len(heading_blocks)} heading blocks:")
    for block in heading_blocks:
        print(f"- {block.type}: {block.content}")
    
    # Extract data from dictionary - find Action Items section
    print("\nDocument Structure from Dictionary:")
    # Find the Action Items section in the dictionary
    document_key = next(key for key in meeting_dict.keys() if "team_meeting_notes" in key)
    document = meeting_dict[document_key]
    
    # Find Action Items heading
    action_items_key = None
    if "children" in document:
        for key in document["children"]:
            if "action_items" in key:
                action_items_key = key
                break
                
    if action_items_key:
        action_items_section = document["children"][action_items_key]
        print(f"Found action items section: {action_items_section['content']}")
        
        # Print paragraphs in this section (action items)
        if "children" in action_items_section:
            print("\nAction Items:")
            for key, item in action_items_section["children"].items():
                if item["type"] == "paragraph":
                    print(f"- {item['content']}")


if __name__ == "__main__":
    main()