"""
Document hierarchy management.
"""
from typing import List, Dict
from dataclasses import dataclass, field
from .models import Block

@dataclass
class Node:
    """Represent a node in the document hierarchy."""
    block: Block
    children: List['Node'] = field(default_factory=list)

class Hierarchy:
    """Handle document structure and hierarchy."""

    def __init__(self):
        """Initialize the document hierarchy handler."""
        self.root = None

    def build_hierarchy(self, blocks: List[Block]) -> Node:
        """
        Build a hierarchical structure from blocks.

        Args:
            blocks: List of document blocks

        Returns:
            Node: Root node of the hierarchy
        """
        # Create root node
        root = Node(Block(id="root", type="root", content="", has_children=True))

        # Track indentation levels
        current_level = {0: root}
        current_depth = 0

        for block in blocks:
            # Determine block level based on type and content
            depth = self._get_block_depth(block)

            # Create new node
            node = Node(block)

            # Add to appropriate parent
            if depth <= current_depth:
                parent_depth = depth - 1
                while parent_depth >= 0 and parent_depth not in current_level:
                    parent_depth -= 1
                if parent_depth >= 0:
                    current_level[parent_depth].children.append(node)
            else:
                current_level[current_depth].children.append(node)

            current_level[depth] = node
            current_depth = depth

        self.root = root
        return root

    def _get_block_depth(self, block: Block) -> int:
        """
        Determine the depth level of a block based on its type.

        Args:
            block: Block to analyze

        Returns:
            int: Depth level of the block
        """
        # Define block type hierarchy
        hierarchy_levels = {
            "heading_1": 1,
            "heading_2": 2,
            "heading_3": 3,
            "paragraph": 4,
            "bulleted_list_item": 4,
            "numbered_list_item": 4,
            "to_do": 4,
        }

        return hierarchy_levels.get(block.type, 4)

    def to_dict(self, node: Node = None) -> Dict:
        """
        Convert hierarchy to dictionary representation.

        Args:
            node: Starting node (defaults to root)

        Returns:
            Dict: Dictionary representation of the hierarchy
        """
        if node is None:
            node = self.root

        result = {
            "id": node.block.id,
            "type": node.block.type,
            "content": node.block.content,
            "children": []
        }

        for child in node.children:
            result["children"].append(self.to_dict(child))

        return result