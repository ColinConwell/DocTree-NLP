"""
Core components for the Notion NLP library.

This module contains the core data models, document hierarchy handling, 
tagging functionality, and custom exceptions for the library.
"""
import logging
import re
import spacy
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Set, Optional, Union, Any
from dataclasses import dataclass, field
from tqdm.auto import tqdm

# Optional imports
try:
    import pandas as pd
except ImportError:
    pd = None  # Will be used for mock testing

logger = logging.getLogger(__name__)

# Source Class ----------------------------------------------------------

class Source(BaseModel):
    """Represent a source of documents (e.g., Notion API account)."""
    id: str
    name: str
    api_type: str = "notion"  # Default to Notion, but extensible for future sources
    documents: List[str] = Field(default_factory=list)  # List of document IDs
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_synced: Optional[datetime] = None
    
    def to_dataframe(self):
        """Convert source metadata to pandas DataFrame."""
        if pd is None:
            logger.warning("pandas not installed; cannot convert to DataFrame")
            return None
        return pd.DataFrame(self.metadata)
    
    def add_document(self, document_id: str) -> None:
        """Add a document ID to this source."""
        if document_id not in self.documents:
            self.documents.append(document_id)

# Block Class -----------------------------------------------------------

class Block(BaseModel):
    """Represent a block of content in a document."""
    id: str
    type: str
    content: str
    has_children: bool = False
    indent_level: int = 0

# Node Class ------------------------------------------------------------

@dataclass
class Node:
    """Represent a node in the document tree."""
    block: Block
    children: List['Node'] = field(default_factory=list)

# DocTree Class ---------------------------------------------------------

class DocTree:
    """Handle document tree structure and traversal."""
    
    def __init__(self):
        """Initialize the document tree handler."""
        self.root = None
    
    def build_tree(self, blocks: List[Block]) -> Node:
        """
        Build a hierarchical tree from blocks.
        
        Args:
            blocks: List of document blocks
            
        Returns:
            Node: Root node of the tree
        """
        # Create root node
        root = Node(Block(id="root", type="root", content="", has_children=True))
        
        # Track indentation levels
        current_level = {0: root}
        current_depth = 0
        
        for block in tqdm(blocks, desc="Building document tree", unit="block"):
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
        Convert tree to dictionary representation.
        
        Args:
            node: Starting node (defaults to root)
            
        Returns:
            Dict: Dictionary representation of the tree
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

    def find_node_by_id(self, block_id: str, node: Node = None) -> Optional[Node]:
        """
        Find a node by its block ID.
        
        Args:
            block_id: The ID of the block to find
            node: Starting node (defaults to root)
            
        Returns:
            Optional[Node]: The found node or None
        """
        if node is None:
            node = self.root
            
        if node.block.id == block_id:
            return node
            
        for child in node.children:
            result = self.find_node_by_id(block_id, child)
            if result:
                return result
                
        return None
    
    def find_nodes_by_type(self, block_type: str, node: Node = None) -> List[Node]:
        """
        Find all nodes of a specific type.
        
        Args:
            block_type: The type of blocks to find
            node: Starting node (defaults to root)
            
        Returns:
            List[Node]: List of matching nodes
        """
        results = []
        if node is None:
            node = self.root
            
        if node.block.type == block_type:
            results.append(node)
            
        for child in node.children:
            results.extend(self.find_nodes_by_type(block_type, child))
                
        return results
    
    def find_nodes_by_content(self, content_pattern: str, node: Node = None) -> List[Node]:
        """
        Find all nodes with content matching a pattern.
        
        Args:
            content_pattern: Pattern to match in block content
            node: Starting node (defaults to root)
            
        Returns:
            List[Node]: List of matching nodes
        """
        results = []
        if node is None:
            node = self.root
            
        if re.search(content_pattern, node.block.content):
            results.append(node)
            
        for child in node.children:
            results.extend(self.find_nodes_by_content(content_pattern, child))
                
        return results

# Document Class --------------------------------------------------------

class Document(BaseModel):
    """
    Represent a document with metadata and content structure.
    
    This is the primary class for working with documents from any source.
    It contains metadata about the document and methods for processing content.
    """
    class Config:
        arbitrary_types_allowed = True  # Allow DocTree as a field type
    
    id: str
    title: str
    created_time: datetime
    last_edited_time: datetime
    last_fetched: Optional[datetime] = None
    etag: Optional[str] = None
    source_id: Optional[str] = None
    blocks: List[Block] = Field(default_factory=list)
    tree: Optional[Any] = None  # Using Any type for DocTree to avoid pydantic errors
    
    def build_tree(self) -> DocTree:
        """
        Build a document tree from blocks.
        
        Returns:
            DocTree: The built document tree
        """
        if not self.blocks:
            logger.warning(f"No blocks found for document {self.id}")
            return DocTree()
            
        tree = DocTree()
        tree.build_tree(self.blocks)
        self.tree = tree
        return tree
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert document to dictionary representation.
        
        Returns:
            Dict: Dictionary representation
        """
        if self.tree is None and self.blocks:
            self.build_tree()
            
        if self.tree is None:
            return {
                "id": self.id,
                "title": self.title,
                "created_time": self.created_time.isoformat(),
                "last_edited_time": self.last_edited_time.isoformat(),
                "content": {}
            }
            
        return {
            "id": self.id,
            "title": self.title,
            "created_time": self.created_time.isoformat(),
            "last_edited_time": self.last_edited_time.isoformat(),
            "content": self._node_to_dict(self.tree.root)
        }
    
    def _node_to_dict(self, node: Node, level: int = 0) -> Dict[str, Any]:
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
                child_dict = self._node_to_dict(child, level)
                result.update(child_dict)
            return result
        
        # Create dict for this node
        block_type = node.block.type
        block_content = node.block.content
        
        # Determine key based on block type
        if block_type.startswith("heading_"):
            key = f"heading_{level}_{self._clean_key(block_content)}"
        elif block_type == "bulleted_list_item":
            key = f"bullet_{level}_{self._clean_key(block_content)}"
        elif block_type == "numbered_list_item":
            key = f"numbered_{level}_{self._clean_key(block_content)}"
        elif block_type == "paragraph":
            key = f"paragraph_{level}_{self._clean_key(block_content)}"
        else:
            key = f"{block_type}_{level}_{self._clean_key(block_content)}"
        
        # Create result dictionary with content as value
        result = {key: {}}
        
        # Add metadata
        result[key]["content"] = block_content
        result[key]["type"] = block_type
        
        # Add children recursively
        if node.children:
            children_dict = {}
            for i, child in enumerate(node.children):
                child_dict = self._node_to_dict(child, level + 1)
                children_dict.update(child_dict)
            
            if children_dict:
                result[key]["children"] = children_dict
        
        return result
    
    def _clean_key(self, text: str) -> str:
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
    
    def to_markdown(self) -> str:
        """
        Convert document to Markdown format.
        
        Returns:
            String containing Markdown representation
        """
        if self.tree is None and self.blocks:
            self.build_tree()
            
        if self.tree is None:
            return f"# {self.title}\n\n(No content available)"
            
        return self._node_to_markdown(self.tree.root)
    
    def _node_to_markdown(self, node: Node, level: int = 0) -> str:
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
        if node.block.type == "root":
            children = tqdm(node.children, desc="Converting to Markdown", unit="node") if level == 0 else node.children
            for child in children:
                result.append(self._node_to_markdown(child, level))
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
            result.append(self._node_to_markdown(child, level + 1))
        
        return "\n".join(result)
    
    def to_rst(self) -> str:
        """
        Convert document to reStructuredText format.
        
        Returns:
            String containing RST representation
        """
        if self.tree is None and self.blocks:
            self.build_tree()
            
        if self.tree is None:
            return f"{self.title}\n{'=' * len(self.title)}\n\n(No content available)"
            
        return self._node_to_rst(self.tree.root)
    
    def _node_to_rst(self, node: Node, level: int = 0) -> str:
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
        if node.block.type == "root":
            children = tqdm(node.children, desc="Converting to RST", unit="node") if level == 0 else node.children
            for child in children:
                result.append(self._node_to_rst(child, level))
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
            result.append(self._node_to_rst(child, level + 1))
        
        return "\n\n".join(result)
    
    @staticmethod
    def load_example(name: str) -> 'Document':
        """
        Load an example document.
        
        Args:
            name: Name of the example document
            
        Returns:
            Document: Loaded document
        """
        import json
        from pathlib import Path
        
        examples_dir = Path(__file__).parent.parent / "examples" / "sample_data"
        file_path = examples_dir / f"{name}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Example document {name} not found at {file_path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Create a Document
        doc = Document(
            id=data.get("id", f"example_{name}"),
            title=data.get("title", name),
            created_time=datetime.fromisoformat(data.get("created_time", datetime.now().isoformat())),
            last_edited_time=datetime.fromisoformat(data.get("last_edited_time", datetime.now().isoformat()))
        )
        
        # Add blocks
        if "blocks" in data:
            for block_data in tqdm(data["blocks"], desc=f"Loading {name} example", unit="block"):
                doc.blocks.append(Block(**block_data))
            
            # Build tree
            doc.build_tree()
        
        return doc
    
    def preview_blocks(self, n: int = 5) -> List[Block]:
        """
        Show the first n blocks of the document.
        
        Args:
            n: Number of blocks to preview
            
        Returns:
            List of preview blocks
        """
        return self.blocks[:n]
    
    def preview_text(self, n_chars: int = 500) -> str:
        """
        Show the first n characters from document content.
        
        Args:
            n_chars: Number of characters to preview
            
        Returns:
            Preview text string
        """
        text = " ".join(block.content for block in self.blocks)
        return text[:n_chars] + "..." if len(text) > n_chars else text
    
    def preview_sentences(self, n: int = 3) -> str:
        """
        Show the first n sentences from document content.
        
        Args:
            n: Number of sentences to preview
            
        Returns:
            Preview text with sentences
        """
        text = " ".join(block.content for block in self.blocks)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        preview = " ".join(sentences[:n])
        
        # Always add ellipsis if there are more than n sentences
        # This ensures consistent behavior for tests
        return preview + "..." if len(sentences) > n else preview
    
    def __repr__(self) -> str:
        """Return string representation for console."""
        preview = self.preview_text(n_chars=100)
        return f"Document(id='{self.id}', title='{self.title}', blocks={len(self.blocks)}, preview='{preview}')"
    
    def _repr_html_(self) -> str:
        """Return HTML representation for Jupyter notebooks."""
        from notionlp.notebook import document_to_html
        return document_to_html(self)

# Tag System ------------------------------------------------------------

class Tag(BaseModel):
    """Represent a tag applied to content."""
    name: str
    type: str
    category: str

class Tagger:
    """Handle document tagging functionality."""
    
    def __init__(self, model: str = "en_core_web_sm"):
        """
        Initialize the tagger.
        
        Args:
            model: spaCy model to use for NLP tasks
        """
        self.nlp = spacy.load(model)
        self.custom_tags: Set[str] = set()

    def add_custom_tags(self, tags: List[str]):
        """
        Add custom tags to the tagger.
        
        Args:
            tags: List of custom tags to add
        """
        self.custom_tags.update(tags)

    def generate_tags(self, block: Block) -> List[Tag]:
        """
        Generate tags for a block of text.
        
        Args:
            block: Block to generate tags for
            
        Returns:
            List[Tag]: Generated tags
        """
        doc = self.nlp(block.content)
        tags = []
        
        # Entity-based tags
        for ent in tqdm(doc.ents, desc="Generating entity tags", unit="entity", leave=False):
            tags.append(Tag(
                name=ent.text.lower(),
                type="entity",
                category=ent.label_
            ))
        
        # Keyword-based tags
        keywords = [
            token.text.lower() for token in doc
            if not token.is_stop and not token.is_punct
            and token.pos_ in ["NOUN", "PROPN", "ADJ"]
        ]
        
        for keyword in tqdm(keywords, desc="Processing keywords", unit="keyword", leave=False):
            if keyword in self.custom_tags:
                tags.append(Tag(
                    name=keyword,
                    type="custom",
                    category="keyword"
                ))
        
        return tags

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict[str, float]: Sentiment scores
        """
        doc = self.nlp(text)
        
        # Simple rule-based sentiment analysis
        positive_words = sum(1 for token in doc if token.pos_ == "ADJ" and token.is_stop == False)
        negative_words = sum(1 for token in doc if token.pos_ == "ADJ" and token.is_stop == True)
        
        total = positive_words + negative_words if (positive_words + negative_words) > 0 else 1
        
        return {
            "positive": positive_words / total,
            "negative": negative_words / total
        }
    
    def tag_document(self, document: Document) -> Dict[str, List[Tag]]:
        """
        Tag all blocks in a document.
        
        Args:
            document: The document to tag
            
        Returns:
            Dict mapping block IDs to lists of tags
        """
        result = {}
        for block in tqdm(document.blocks, desc="Tagging document", unit="block"):
            result[block.id] = self.generate_tags(block)
        return result

# For backward compatibility
class Hierarchy(DocTree):
    """Legacy Hierarchy class for backward compatibility."""
    
    def build_hierarchy(self, blocks: List[Block]) -> Node:
        """Build hierarchy from blocks (legacy method)."""
        return self.build_tree(blocks)