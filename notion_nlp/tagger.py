"""
Document tagging system.
"""
from typing import List, Dict, Set
import spacy
from .models import Tag, Block

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
        for ent in doc.ents:
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
        
        for keyword in keywords:
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
