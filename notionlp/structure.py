"""
Core components for the Notion NLP library.

This module contains the core data models, document hierarchy handling, 
tagging functionality, and custom exceptions for the library.
"""
import logging
import spacy
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from tqdm.auto import tqdm

logger = logging.getLogger(__name__)

# Data Structures ----------------------------------------------------

class Document(BaseModel):
    """Represent a Notion document."""
    id: str
    title: str
    created_time: datetime
    last_edited_time: datetime
    last_fetched: Optional[datetime] = None
    etag: Optional[str] = None

class Tag(BaseModel):
    """Represent a tag applied to content."""
    name: str
    type: str
    category: str

class Block(BaseModel):
    """Represent a block of content in a Notion document."""
    id: str
    type: str
    content: str
    has_children: bool = False
    indent_level: int = 0


# Document Hierarchy -------------------------------------------------

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

        for block in tqdm(blocks, desc="Building document hierarchy", unit="block"):
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

# Tagging System ------------------------------------------------------

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