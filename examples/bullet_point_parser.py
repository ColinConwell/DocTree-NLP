"""
Example of parsing bullet points into nested dictionaries.

This example demonstrates how to convert hierarchical bullet points
into a nested dictionary structure.
"""
import re
import json
from typing import List, Dict, Any
from notion_nlp import Hierarchy
from notion_nlp.models import Block

def parse_bullet_points(text: str) -> Dict[str, Any]:
    """
    Parse bullet points from text into a nested dictionary.
    
    Args:
        text: Text containing bullet points
        
    Returns:
        Dict[str, Any]: Nested dictionary representing the bullet point hierarchy
    """
    # Split text into lines and remove empty lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Create blocks from lines
    blocks = []
    for i, line in enumerate(lines):
        # Determine indentation level
        indent_match = re.match(r'^(\s*)', line)
        indent_level = len(indent_match.group(1)) // 2 if indent_match else 0
        
        # Remove bullet markers and leading whitespace
        content = re.sub(r'^\s*[\•\-\*]\s*', '', line)
        
        # Create block
        block = Block(
            id=f"block_{i}",
            type="bulleted_list_item",
            content=content,
            has_children=False,
            indent_level=indent_level
        )
        blocks.append(block)
    
    # Build hierarchy
    hierarchy = Hierarchy()
    root = hierarchy.build_hierarchy(blocks)
    
    # Convert hierarchy to dictionary
    hierarchy_dict = hierarchy.to_dict()
    
    # Transform to a more natural nested dictionary
    return _transform_hierarchy_to_dict(hierarchy_dict)

def _transform_hierarchy_to_dict(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform hierarchy node to a more natural dictionary structure.
    
    Args:
        node: Hierarchy node dictionary
        
    Returns:
        Dict[str, Any]: Transformed dictionary
    """
    # Skip root node
    if node["type"] == "root":
        result = {}
        for child in node["children"]:
            child_dict = _transform_hierarchy_to_dict(child)
            result.update(child_dict)
        return result
    
    # Process content node
    result = {}
    if node["content"]:
        # Check if content has a key-value structure
        key_value_match = re.match(r'^([^:]+):\s*(.+)$', node["content"])
        
        if key_value_match:
            # Key-value pair
            key, value = key_value_match.groups()
            if node["children"]:
                # Key with nested dictionary
                child_dict = {}
                for child in node["children"]:
                    child_dict.update(_transform_hierarchy_to_dict(child))
                result[key.strip()] = {
                    "value": value.strip(),
                    "children": child_dict
                }
            else:
                # Simple key-value pair
                result[key.strip()] = value.strip()
        else:
            # Content without explicit key
            if node["children"]:
                # Content with nested items
                child_dict = {}
                for child in node["children"]:
                    child_dict.update(_transform_hierarchy_to_dict(child))
                result[node["content"]] = child_dict
            else:
                # Leaf content
                result[f"item_{node['id']}"] = node["content"]
    
    return result

def main():
    """Main example function."""
    try:
        # Sample bullet point text
        sample_text = """
        • Project Overview
          • Title: NotioNLP Toolkit
          • Version: 0.1.0
          • Description: NLP tools for Notion documents
        • Features
          • Document Processing
            • Content extraction
            • Block parsing
          • NLP Capabilities
            • Entity recognition
            • Keyword extraction
            • Summarization
        • Requirements
          • Python 3.11+
          • Dependencies:
            • spaCy
            • Notion API client
            • Pydantic
        """
        
        print("Sample bullet point text:")
        print(sample_text)
        
        # Parse bullet points
        print("\nParsing bullet points...")
        result = parse_bullet_points(sample_text)
        
        # Display result
        print("\nNested dictionary structure:")
        print(json.dumps(result, indent=2))
        
        # Integration with NotionNLP
        print("\nIntegration with NotionNLP:")
        
        # Create blocks manually to simulate Notion content
        blocks = []
        lines = [line for line in sample_text.splitlines() if line.strip()]
        
        for i, line in enumerate(lines):
            indent_match = re.match(r'^(\s*)', line)
            indent_level = len(indent_match.group(1)) // 2 if indent_match else 0
            content = re.sub(r'^\s*[\•\-\*]\s*', '', line)
            
            block = Block(
                id=f"block_{i}",
                type="bulleted_list_item",
                content=content,
                has_children=False,
                indent_level=indent_level
            )
            blocks.append(block)
        
        # Build hierarchy using Hierarchy
        hierarchy = Hierarchy()
        root = hierarchy.build_hierarchy(blocks)
        
        # Convert to dictionary
        hierarchy_dict = hierarchy.to_dict()
        
        print("\nHierarchy structure:")
        print(json.dumps(hierarchy_dict, indent=2))
        
        # Transform to natural nested dictionary
        transformed = _transform_hierarchy_to_dict(hierarchy_dict)
        
        print("\nTransformed structure:")
        print(json.dumps(transformed, indent=2))
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
