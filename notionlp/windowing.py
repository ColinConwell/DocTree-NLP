"""
Windowing implementation for large document trees.

This module provides windowing functionality for displaying and navigating
large document trees with minimal memory usage.
"""

import logging
from typing import List, Dict, Any, Optional, Generator, Tuple
from dataclasses import dataclass

from .structure import Document, Block, DocTree, Node
from .defaults import get_default

logger = logging.getLogger(__name__)

@dataclass
class DocumentWindow:
    """Represent a window view into a large document."""
    
    document_id: str
    document_title: str
    offset: int
    limit: int
    total_blocks: int
    blocks: List[Block]
    has_previous: bool
    has_next: bool
    
    @property
    def start_index(self) -> int:
        """Get the start index of this window."""
        return self.offset
    
    @property
    def end_index(self) -> int:
        """Get the end index of this window."""
        return min(self.offset + self.limit, self.total_blocks)
    
    @property
    def is_first_window(self) -> bool:
        """Check if this is the first window."""
        return self.offset == 0
    
    @property
    def is_last_window(self) -> bool:
        """Check if this is the last window."""
        return self.offset + self.limit >= self.total_blocks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert window to dictionary for serialization."""
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "offset": self.offset,
            "limit": self.limit,
            "total_blocks": self.total_blocks,
            "window_size": len(self.blocks),
            "start_index": self.start_index,
            "end_index": self.end_index,
            "has_previous": self.has_previous,
            "has_next": self.has_next,
            "blocks": [
                {
                    "id": block.id,
                    "type": block.type,
                    "content": block.content,
                    "has_children": block.has_children,
                    "indent_level": block.indent_level
                }
                for block in self.blocks
            ]
        }
    
    def to_markdown(self) -> str:
        """Convert window content to Markdown."""
        lines = [f"# {self.document_title} (Window {self.start_index}-{self.end_index} of {self.total_blocks})"]
        
        for block in self.blocks:
            if block.type.startswith("heading_"):
                heading_level = int(block.type[-1]) + 1  # Adjust for the document title
                lines.append(f"{'#' * heading_level} {block.content}")
            elif block.type == "bulleted_list_item":
                lines.append(f"- {block.content}")
            elif block.type == "numbered_list_item":
                lines.append(f"1. {block.content}")
            elif block.type == "paragraph":
                lines.append(f"{block.content}\n")
            elif block.type == "code":
                lines.append(f"```\n{block.content}\n```")
            elif block.type == "quote":
                lines.append(f"> {block.content}")
            else:
                lines.append(block.content)
        
        if self.has_next:
            lines.append("\n---\n*More content available in next window*")
        
        return "\n".join(lines)
    
    def _repr_html_(self) -> str:
        """HTML representation for Jupyter notebooks."""
        html = [
            f"<h1>{self.document_title}</h1>",
            f"<div class='document-window-info'>Window {self.start_index}-{self.end_index} of {self.total_blocks} blocks</div>",
            "<div class='document-window-content'>"
        ]
        
        for block in self.blocks:
            if block.type.startswith("heading_"):
                heading_level = int(block.type[-1])
                html.append(f"<h{heading_level}>{block.content}</h{heading_level}>")
            elif block.type == "bulleted_list_item":
                html.append(f"<ul><li>{block.content}</li></ul>")
            elif block.type == "numbered_list_item":
                html.append(f"<ol><li>{block.content}</li></ol>")
            elif block.type == "paragraph":
                html.append(f"<p>{block.content}</p>")
            elif block.type == "code":
                html.append(f"<pre><code>{block.content}</code></pre>")
            elif block.type == "quote":
                html.append(f"<blockquote>{block.content}</blockquote>")
            else:
                html.append(f"<div>{block.content}</div>")
        
        html.append("</div>")
        
        # Navigation controls
        html.append("<div class='document-window-navigation'>")
        if self.has_previous:
            html.append(f"<span class='window-previous'>« Previous {self.limit} blocks</span>")
        if self.has_next:
            html.append(f"<span class='window-next'>Next {self.limit} blocks »</span>")
        html.append("</div>")
        
        return "".join(html)


class DocumentWindower:
    """
    Handle windowing for large documents.
    
    This class provides tools for navigating large documents by splitting them
    into smaller windows of content.
    """
    
    def __init__(self, default_window_size: Optional[int] = None):
        """
        Initialize the document windower.
        
        Args:
            default_window_size: Default number of blocks per window
        """
        self.default_window_size = default_window_size or get_default('document.window_size')
    
    def create_window(
        self, 
        document: Document, 
        offset: int = 0,
        limit: Optional[int] = None
    ) -> DocumentWindow:
        """
        Create a window view into a document.
        
        Args:
            document: The document to create a window for
            offset: Starting index of the window
            limit: Maximum number of blocks to include
            
        Returns:
            DocumentWindow: A window into the document
        """
        if limit is None:
            limit = self.default_window_size
        
        total_blocks = len(document.blocks)
        
        # Validate offset
        if offset < 0:
            offset = 0
        elif offset >= total_blocks:
            offset = max(0, total_blocks - limit)
        
        # Get the window blocks
        end_idx = min(offset + limit, total_blocks)
        window_blocks = document.blocks[offset:end_idx]
        
        return DocumentWindow(
            document_id=document.id,
            document_title=document.title,
            offset=offset,
            limit=limit,
            total_blocks=total_blocks,
            blocks=window_blocks,
            has_previous=offset > 0,
            has_next=end_idx < total_blocks
        )
    
    def get_next_window(self, current_window: DocumentWindow, document: Document) -> DocumentWindow:
        """
        Get the next window after the current one.
        
        Args:
            current_window: The current window
            document: The document
            
        Returns:
            DocumentWindow: The next window
        """
        new_offset = current_window.offset + current_window.limit
        return self.create_window(document, new_offset, current_window.limit)
    
    def get_previous_window(self, current_window: DocumentWindow, document: Document) -> DocumentWindow:
        """
        Get the previous window before the current one.
        
        Args:
            current_window: The current window
            document: The document
            
        Returns:
            DocumentWindow: The previous window
        """
        new_offset = max(0, current_window.offset - current_window.limit)
        return self.create_window(document, new_offset, current_window.limit)
    
    def generate_all_windows(
        self, 
        document: Document, 
        window_size: Optional[int] = None
    ) -> Generator[DocumentWindow, None, None]:
        """
        Generate all windows for a document.
        
        Args:
            document: The document to window
            window_size: Size of each window
            
        Yields:
            DocumentWindow: Each window in sequence
        """
        if window_size is None:
            window_size = self.default_window_size
        
        total_blocks = len(document.blocks)
        
        for offset in range(0, total_blocks, window_size):
            yield self.create_window(document, offset, window_size)
    
    def find_block_window(
        self, 
        document: Document, 
        block_id: str,
        window_size: Optional[int] = None,
        context_blocks: int = 0
    ) -> Optional[DocumentWindow]:
        """
        Find a window containing a specific block.
        
        Args:
            document: The document to search
            block_id: ID of the block to find
            window_size: Size of the window
            context_blocks: Number of blocks to include before the target block
            
        Returns:
            Optional[DocumentWindow]: Window containing the block, or None if not found
        """
        if window_size is None:
            window_size = self.default_window_size
        
        # Find the block index
        block_index = None
        for i, block in enumerate(document.blocks):
            if block.id == block_id:
                block_index = i
                break
        
        if block_index is None:
            logger.warning(f"Block {block_id} not found in document {document.id}")
            return None
        
        # Calculate window offset with context
        offset = max(0, block_index - context_blocks)
        
        return self.create_window(document, offset, window_size)
    
    def find_text_window(
        self, 
        document: Document, 
        search_text: str,
        window_size: Optional[int] = None,
        case_sensitive: bool = False,
        context_blocks: int = 0
    ) -> Optional[DocumentWindow]:
        """
        Find a window containing specific text.
        
        Args:
            document: The document to search
            search_text: Text to search for
            window_size: Size of the window
            case_sensitive: Whether the search is case sensitive
            context_blocks: Number of blocks to include before the matching block
            
        Returns:
            Optional[DocumentWindow]: Window containing the text, or None if not found
        """
        if window_size is None:
            window_size = self.default_window_size
        
        # Normalize search text for case insensitive search
        if not case_sensitive:
            search_text = search_text.lower()
        
        # Find the first matching block
        block_index = None
        for i, block in enumerate(document.blocks):
            block_content = block.content if case_sensitive else block.content.lower()
            if search_text in block_content:
                block_index = i
                break
        
        if block_index is None:
            logger.warning(f"Text '{search_text}' not found in document {document.id}")
            return None
        
        # Calculate window offset with context
        offset = max(0, block_index - context_blocks)
        
        return self.create_window(document, offset, window_size)


class TreeWindower:
    """
    Handle windowing for document trees.
    
    This class provides tools for navigating large document trees by splitting them
    into smaller windows based on tree structure.
    """
    
    def __init__(self, default_nodes_per_window: Optional[int] = None):
        """
        Initialize the tree windower.
        
        Args:
            default_nodes_per_window: Default number of nodes per window
        """
        self.default_nodes_per_window = default_nodes_per_window or get_default('document.tree_nodes_per_window')
    
    def _collect_nodes(self, node: Node) -> List[Node]:
        """
        Collect all nodes in a tree.
        
        Args:
            node: Root node
            
        Returns:
            List[Node]: Flat list of all nodes
        """
        result = [node]
        
        for child in node.children:
            result.extend(self._collect_nodes(child))
        
        return result
    
    def window_tree(
        self, 
        document: Document, 
        offset: int = 0, 
        limit: Optional[int] = None
    ) -> Tuple[List[Node], bool, bool]:
        """
        Create a window view into a document tree.
        
        Args:
            document: The document to create a window for
            offset: Starting index in the flattened node list
            limit: Maximum number of nodes to include
            
        Returns:
            Tuple[List[Node], bool, bool]: (windowed nodes, has_previous, has_next)
        """
        if limit is None:
            limit = self.default_nodes_per_window
        
        # Ensure tree is built
        if document.tree is None:
            document.build_tree()
        
        if document.tree is None or document.tree.root is None:
            return [], False, False
        
        # Flatten the tree
        all_nodes = self._collect_nodes(document.tree.root)
        total_nodes = len(all_nodes)
        
        # Validate offset
        if offset < 0:
            offset = 0
        elif offset >= total_nodes:
            offset = max(0, total_nodes - limit)
        
        # Get window nodes
        end_idx = min(offset + limit, total_nodes)
        window_nodes = all_nodes[offset:end_idx]
        
        has_previous = offset > 0
        has_next = end_idx < total_nodes
        
        return window_nodes, has_previous, has_next
    
    def find_node_window(
        self, 
        document: Document, 
        node_id: str,
        context_nodes: int = 5,
        limit: Optional[int] = None
    ) -> Tuple[List[Node], bool, bool]:
        """
        Find a window containing a specific node.
        
        Args:
            document: The document to search
            node_id: ID of the node to find
            context_nodes: Number of nodes to include before the target node
            limit: Size of the window
            
        Returns:
            Tuple[List[Node], bool, bool]: (windowed nodes, has_previous, has_next)
        """
        if limit is None:
            limit = self.default_nodes_per_window
        
        # Ensure tree is built
        if document.tree is None:
            document.build_tree()
        
        if document.tree is None or document.tree.root is None:
            return [], False, False
        
        # Flatten the tree
        all_nodes = self._collect_nodes(document.tree.root)
        
        # Find the node
        node_index = None
        for i, node in enumerate(all_nodes):
            if node.block.id == node_id:
                node_index = i
                break
        
        if node_index is None:
            logger.warning(f"Node {node_id} not found in document {document.id}")
            return [], False, False
        
        # Calculate window with context
        offset = max(0, node_index - context_nodes)
        
        return self.window_tree(document, offset, limit)