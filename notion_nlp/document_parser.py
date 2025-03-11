"""
Document parsing utilities for NotioNLPToolkit.

This module provides convenience functions for parsing Notion documents
into various formats including dictionaries, markdown, and RST.
"""
from typing import Dict, Any, List, Optional, Union
import os
import json
import re
from pathlib import Path

from .models import Block, Document
from .hierarchy import Hierarchy, Node


def doc_to_dict(document: Union[Document, List[Block], Hierarchy]) -> Dict[str, Any]:
    """
    Convert a Notion document into a nested dictionary following the document hierarchy.
    
    Args:
        document: Either a Document object, a list of Block objects, or a Hierarchy object
        
    Returns:
        A nested dictionary representation of the document
    """
    # Convert to Hierarchy if needed
    hierarchy = None
    if isinstance(document, Document):
        # Assuming Document has blocks attribute
        if hasattr(document, 'blocks'):
            hierarchy = Hierarchy()
            hierarchy.build_hierarchy(document.blocks)
    elif isinstance(document, list):
        # Assume it's a list of blocks
        hierarchy = Hierarchy()
        hierarchy.build_hierarchy(document)
    elif isinstance(document, Hierarchy):
        hierarchy = document
    else:
        raise TypeError(f"Expected Document, List[Block], or Hierarchy, got {type(document)}")
    
    if not hierarchy or not hierarchy.root or not hierarchy.root.children:
        return {}
    
    return _node_to_dict(hierarchy.root)


def _node_to_dict(node: Node, level: int = 0) -> Dict[str, Any]:
    """
    Recursively convert a Node and its children to a dictionary.
    
    Args:
        node: The Node to convert
        level: Current nesting level
        
    Returns:
        A dictionary representing the node and its children
    """
    # Skip root node which is a placeholder
    if node.block.type == "root" and node.children:
        result = {}
        for i, child in enumerate(node.children):
            child_dict = _node_to_dict(child, level)
            result.update(child_dict)
        return result
    
    # Create dict for this node
    block_type = node.block.type
    block_content = node.block.content
    
    # Determine key based on block type
    if block_type.startswith("heading_"):
        key = f"heading_{level}_{_clean_key(block_content)}"
    elif block_type == "bulleted_list_item":
        key = f"bullet_{level}_{_clean_key(block_content)}"
    elif block_type == "numbered_list_item":
        key = f"numbered_{level}_{_clean_key(block_content)}"
    elif block_type == "paragraph":
        key = f"paragraph_{level}_{_clean_key(block_content)}"
    else:
        key = f"{block_type}_{level}_{_clean_key(block_content)}"
    
    # Create result dictionary with content as value
    result = {key: {}}
    
    # Add metadata
    result[key]["content"] = block_content
    result[key]["type"] = block_type
    
    # Add children recursively
    if node.children:
        children_dict = {}
        for i, child in enumerate(node.children):
            child_dict = _node_to_dict(child, level + 1)
            children_dict.update(child_dict)
        
        if children_dict:
            result[key]["children"] = children_dict
    
    return result


def _clean_key(text: str) -> str:
    """
    Clean text to be used as a dictionary key.
    
    Args:
        text: Text to clean
        
    Returns:
        A cleaned string suitable for use as a dictionary key
    """
    # Take first few words
    shortened = " ".join(text.split()[:3])
    # Remove special characters
    cleaned = re.sub(r'[^\w\s]', '', shortened)
    # Replace spaces with underscores
    return cleaned.lower().replace(' ', '_')


def export_to_markdown(document: Union[Document, List[Block], Hierarchy]) -> str:
    """
    Convert a Notion document to Markdown format.
    
    Args:
        document: Either a Document object, a list of Block objects, or a Hierarchy object
        
    Returns:
        String containing Markdown representation of the document
    """
    # Convert to Hierarchy if needed
    hierarchy = None
    if isinstance(document, Document):
        if hasattr(document, 'blocks'):
            hierarchy = Hierarchy()
            hierarchy.build_hierarchy(document.blocks)
    elif isinstance(document, list):
        hierarchy = Hierarchy()
        hierarchy.build_hierarchy(document)
    elif isinstance(document, Hierarchy):
        hierarchy = document
    else:
        raise TypeError(f"Expected Document, List[Block], or Hierarchy, got {type(document)}")
    
    if not hierarchy or not hierarchy.root:
        return ""
    
    return _node_to_markdown(hierarchy.root)


def _node_to_markdown(node: Node, level: int = 0) -> str:
    """
    Recursively convert a Node and its children to Markdown.
    
    Args:
        node: The Node to convert
        level: Current nesting level
        
    Returns:
        A string with Markdown representation
    """
    result = []
    
    # Skip root node which is a placeholder
    if node.block is None:
        for child in node.children:
            result.append(_node_to_markdown(child, level))
        return "\n".join(result)
    
    # Process current block
    block_type = node.block.type
    content = node.block.content
    
    if block_type.startswith("heading_"):
        heading_level = int(block_type[-1])
        result.append(f"{'#' * heading_level} {content}")
    elif block_type == "bulleted_list_item":
        indent = "  " * level
        result.append(f"{indent}- {content}")
    elif block_type == "numbered_list_item":
        indent = "  " * level
        result.append(f"{indent}1. {content}")
    elif block_type == "paragraph":
        result.append(f"{content}")
    elif block_type == "code":
        result.append(f"```\n{content}\n```")
    elif block_type == "quote":
        result.append(f"> {content}")
    elif block_type == "divider":
        result.append("---")
    else:
        # Default handling
        result.append(content)
    
    # Process children
    for child in node.children:
        result.append(_node_to_markdown(child, level + 1))
    
    return "\n".join(result)


def export_to_rst(document: Union[Document, List[Block], Hierarchy]) -> str:
    """
    Convert a Notion document to reStructuredText format.
    
    Args:
        document: Either a Document object, a list of Block objects, or a Hierarchy object
        
    Returns:
        String containing RST representation of the document
    """
    # Convert to Hierarchy if needed
    hierarchy = None
    if isinstance(document, Document):
        if hasattr(document, 'blocks'):
            hierarchy = Hierarchy()
            hierarchy.build_hierarchy(document.blocks)
    elif isinstance(document, list):
        hierarchy = Hierarchy()
        hierarchy.build_hierarchy(document)
    elif isinstance(document, Hierarchy):
        hierarchy = document
    else:
        raise TypeError(f"Expected Document, List[Block], or Hierarchy, got {type(document)}")
    
    if not hierarchy or not hierarchy.root:
        return ""
    
    return _node_to_rst(hierarchy.root)


def _node_to_rst(node: Node, level: int = 0) -> str:
    """
    Recursively convert a Node and its children to RST.
    
    Args:
        node: The Node to convert
        level: Current nesting level
        
    Returns:
        A string with RST representation
    """
    result = []
    
    # Skip root node which is a placeholder
    if node.block is None:
        for child in node.children:
            result.append(_node_to_rst(child, level))
        return "\n".join(result)
    
    # Process current block
    block_type = node.block.type
    content = node.block.content
    
    if block_type.startswith("heading_"):
        heading_level = int(block_type[-1])
        heading_chars = ["=", "-", "~", "\"", "'", "`"][min(heading_level - 1, 5)]
        result.append(f"{content}\n{heading_chars * len(content)}")
    elif block_type == "bulleted_list_item":
        indent = "  " * level
        result.append(f"{indent}* {content}")
    elif block_type == "numbered_list_item":
        indent = "  " * level
        result.append(f"{indent}#. {content}")
    elif block_type == "paragraph":
        result.append(f"{content}")
    elif block_type == "code":
        result.append(f".. code-block::\n\n   {content.replace(chr(10), chr(10) + '   ')}")
    elif block_type == "quote":
        lines = content.split(chr(10))
        quoted_lines = [f"   {line}" for line in lines]
        result.append("\n".join(quoted_lines))
    elif block_type == "divider":
        result.append("\n----\n")
    else:
        # Default handling
        result.append(content)
    
    # Process children
    for child in node.children:
        result.append(_node_to_rst(child, level + 1))
    
    return "\n\n".join(result)


def load_example_document(name: str) -> List[Block]:
    """
    Load an example document from the examples/data directory.
    
    Args:
        name: Name of the example document (without extension)
        
    Returns:
        List of Block objects constructed from the example document
    """
    examples_dir = Path(__file__).parent.parent / "examples" / "data"
    file_path = examples_dir / f"{name}.json"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Example document {name} not found at {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Convert the JSON data to Block objects
    blocks = []
    for block_data in data:
        blocks.append(Block(**block_data))
    
    return blocks