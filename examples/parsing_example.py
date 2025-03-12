"""
Simple example demonstrating how to use the document parsing features.
"""
from notionlp import Hierarchy
from notionlp.parsers import (
    load_example_document, 
    doc_to_dict, 
    export_to_markdown,
    export_to_rst
)

# Load example document
blocks = load_example_document("meeting_notes")
print(f"Loaded {len(blocks)} blocks")

# Create hierarchy
hierarchy = Hierarchy()
hierarchy.build_hierarchy(blocks)

# Convert to dictionary
doc_dict = doc_to_dict(hierarchy)
print("\nDictionary structure:")
for key in doc_dict:
    print(f"- {key}")
    if "children" in doc_dict[key]:
        for child_key in doc_dict[key]["children"]:
            print(f"  - {child_key}")

# Convert to markdown
md = export_to_markdown(hierarchy)
print("\nMarkdown preview (first 200 chars):")
print(md[:200] + "...")

# Convert to RST
rst = export_to_rst(hierarchy)
print("\nRST preview (first 200 chars):")
print(rst[:200] + "...")

# You can also use the functions directly with blocks
md_direct = export_to_markdown(blocks)
print("\nMarkdown generated directly from blocks (first 200 chars):")
print(md_direct[:200] + "...")