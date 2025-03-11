"""
Tests for the tagging system implementation.
"""
import pytest
from notion_nlp.tags import Tagger
from notion_nlp.models import Block, Tag

@pytest.fixture
def tagger():
    """Create a tagger instance."""
    return Tagger()

def test_generate_tags(tagger):
    """Test generating tags for content."""
    block = Block(
        id="1",
        type="paragraph",
        content="Apple is a technology company in California.",
        has_children=False
    )
    
    tags = tagger.generate_tags(block)
    
    assert isinstance(tags, list)
    assert all(isinstance(tag, Tag) for tag in tags)
    assert any(tag.name.lower() == "apple" for tag in tags)
    assert any(tag.name.lower() == "california" for tag in tags)

def test_custom_tags(tagger):
    """Test custom tag functionality."""
    custom_tags = ["important", "review"]
    tagger.add_custom_tags(custom_tags)
    
    block = Block(
        id="1",
        type="paragraph",
        content="This is important content for review.",
        has_children=False
    )
    
    tags = tagger.generate_tags(block)
    
    assert any(tag.name == "important" for tag in tags)
    assert any(tag.name == "review" for tag in tags)

def test_sentiment_analysis(tagger):
    """Test sentiment analysis."""
    text = "This is a great product with amazing features."
    
    sentiment = tagger.analyze_sentiment(text)
    
    assert isinstance(sentiment, dict)
    assert "positive" in sentiment
    assert "negative" in sentiment
    assert sentiment["positive"] + sentiment["negative"] == 1.0
