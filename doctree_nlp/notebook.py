"""
Jupyter notebook integration for DocTree-NLP library.

This module provides interactive HTML widgets and rich display 
capabilities for Jupyter notebooks.
"""
import html
from IPython.display import HTML, display
from typing import List, Dict, Any, Optional

def document_to_html(document) -> str:
    """
    Convert a Document to a rich HTML representation.
    
    Args:
        document: Document instance to display
        
    Returns:
        String containing HTML representation
    """
    # Base styles similar to modern scikit-learn/traitlets style
    styles = """
    <style>
        .notionlp-doc {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 1em;
            margin: 1em 0;
            background: #fcfcfc;
        }
        .notionlp-header {
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 0.5em;
        }
        .notionlp-metadata {
            color: #7f8c8d;
            font-size: 0.9em;
            margin: 0.5em 0;
        }
        .notionlp-preview {
            margin-top: 1em;
            border-left: 3px solid #3498db;
            padding-left: 1em;
        }
        .notionlp-preview-block {
            margin: 0.5em 0;
            padding: 0.5em;
            background: #f8f9fa;
            border-radius: 3px;
        }
        .notionlp-block-heading {
            font-weight: 600;
            color: #2980b9;
        }
    </style>
    """
    
    # Basic document info
    html_parts = [styles]
    html_parts.append('<div class="notionlp-doc">')
    html_parts.append(f'<div class="notionlp-header">{html.escape(document.title)}</div>')
    
    # Metadata section
    html_parts.append('<div class="notionlp-metadata">')
    html_parts.append(f'ID: {html.escape(document.id)}<br>')
    html_parts.append(f'Created: {document.created_time.strftime("%Y-%m-%d %H:%M")}<br>')
    html_parts.append(f'Last Edited: {document.last_edited_time.strftime("%Y-%m-%d %H:%M")}<br>')
    html_parts.append(f'Blocks: {len(document.blocks)}')
    html_parts.append('</div>')
    
    # Preview section with first few blocks
    if document.blocks:
        html_parts.append('<div class="notionlp-preview">')
        html_parts.append('<div>Preview:</div>')
        for i, block in enumerate(document.blocks[:5]):
            html_parts.append(f'<div class="notionlp-preview-block">')
            if block.type.startswith('heading'):
                html_parts.append(f'<span class="notionlp-block-heading">[{block.type}]</span> {html.escape(block.content)}')
            else:
                html_parts.append(f'<span>[{block.type}]</span> {html.escape(block.content)}')
            html_parts.append('</div>')
        
        if len(document.blocks) > 5:
            html_parts.append(f'<div>... {len(document.blocks) - 5} more blocks</div>')
        html_parts.append('</div>')
    
    html_parts.append('</div>')
    return ''.join(html_parts)

def display_document(document) -> None:
    """
    Display a document in Jupyter notebook.
    
    Args:
        document: Document instance to display
    """
    display(HTML(document_to_html(document)))

def display_document_tree(document) -> None:
    """
    Display an interactive tree view of document structure.
    
    Args:
        document: Document instance to display as a tree
    """
    if not document.tree:
        document.build_tree()
    
    # Simple recursive tree implementation with collapsible sections
    js_code = """
    <script>
    function toggleNode(id) {
        const el = document.getElementById(id);
        if (el.style.display === 'none') {
            el.style.display = 'block';
            document.getElementById(id + '-toggle').textContent = '▼';
        } else {
            el.style.display = 'none';
            document.getElementById(id + '-toggle').textContent = '►';
        }
    }
    </script>
    """
    
    styles = """
    <style>
    .tree-node {
        margin-left: 20px;
    }
    .tree-content {
        display: inline-block;
        padding: 2px 5px;
    }
    .toggle-btn {
        cursor: pointer;
        color: #2980b9;
        display: inline-block;
        width: 15px;
        text-align: center;
    }
    .tree-item {
        margin: 2px 0;
    }
    .heading-1 { font-size: 1.5em; font-weight: bold; }
    .heading-2 { font-size: 1.3em; font-weight: bold; }
    .heading-3 { font-size: 1.1em; font-weight: bold; }
    </style>
    """
    
    html_output = [js_code, styles, '<div class="tree-root">']
    
    # Recursively build tree HTML
    next_id = 0
    
    def build_tree_html(node, indent=0):
        nonlocal next_id
        node_id = f"tree-node-{next_id}"
        toggle_id = f"{node_id}-toggle"
        next_id += 1
        
        if node.block.type == "root":
            # Skip the root node itself, but process children
            for child in node.children:
                build_tree_html(child, indent)
            return
        
        block_type_class = f"block-{node.block.type.replace('_', '-')}"
        html_output.append(f'<div class="tree-item {block_type_class}">')
        
        # Only show toggle button if there are children
        if node.children:
            html_output.append(
                f'<span id="{toggle_id}" class="toggle-btn" onclick="toggleNode(\'{node_id}\')">▼</span>'
            )
        else:
            html_output.append('<span class="toggle-btn" style="visibility:hidden">•</span>')
        
        # Node content
        style_class = node.block.type if node.block.type in ["heading_1", "heading_2", "heading_3"] else ""
        html_output.append(
            f'<span class="tree-content {style_class}">[{node.block.type}] {html.escape(node.block.content)}</span>'
        )
        html_output.append('</div>')
        
        # Children container
        if node.children:
            html_output.append(f'<div id="{node_id}" class="tree-node">')
            for child in node.children:
                build_tree_html(child, indent + 1)
            html_output.append('</div>')
    
    if document.tree and document.tree.root:
        build_tree_html(document.tree.root)
    
    html_output.append('</div>')
    display(HTML(''.join(html_output)))

def document_to_table_html(document) -> str:
    """
    Convert a Document's blocks to an HTML table.
    
    Args:
        document: Document instance to display
        
    Returns:
        String containing HTML table representation
    """
    styles = """
    <style>
        .notionlp-table {
            width: 100%;
            border-collapse: collapse;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 1em 0;
        }
        .notionlp-table th {
            background-color: #f8f9fa;
            color: #2c3e50;
            text-align: left;
            padding: 8px;
            border-bottom: 2px solid #ddd;
        }
        .notionlp-table td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }
        .notionlp-table tr:hover {
            background-color: #f5f5f5;
        }
        .notionlp-table-caption {
            caption-side: top;
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 0.5em;
            color: #2c3e50;
        }
    </style>
    """
    
    html_parts = [styles]
    html_parts.append('<table class="notionlp-table">')
    html_parts.append(f'<caption class="notionlp-table-caption">{html.escape(document.title)}</caption>')
    
    # Table header
    html_parts.append('<thead><tr>')
    html_parts.append('<th>#</th><th>Type</th><th>Content</th>')
    html_parts.append('</tr></thead>')
    
    # Table body
    html_parts.append('<tbody>')
    for i, block in enumerate(document.blocks):
        html_parts.append('<tr>')
        html_parts.append(f'<td>{i+1}</td>')
        html_parts.append(f'<td>{html.escape(block.type)}</td>')
        
        # Truncate very long content
        content = block.content
        if len(content) > 200:
            content = content[:197] + '...'
            
        html_parts.append(f'<td>{html.escape(content)}</td>')
        html_parts.append('</tr>')
    html_parts.append('</tbody>')
    
    html_parts.append('</table>')
    return ''.join(html_parts)

def display_document_table(document) -> None:
    """
    Display a document's blocks as a table in Jupyter notebook.
    
    Args:
        document: Document instance to display
    """
    display(HTML(document_to_table_html(document)))