"""
Test the tagging module.
"""
import pytest
from unittest.mock import MagicMock, patch

from notion_nlp.core import Tagger, Block, Tag

@pytest.fixture
def tagger():
    """Return a Tagger instance."""
    with patch("spacy.load") as mock_load:
        # Create a mock spaCy model
        mock_nlp = MagicMock()
        mock_load.return_value = mock_nlp
        
        # Mock spaCy output
        mock_doc = MagicMock()
        mock_ent = MagicMock()
        mock_ent.text = "test entity"
        mock_ent.label_ = "ORG"
        mock_doc.ents = [mock_ent]
        
        mock_token = MagicMock()
        mock_token.text = "keyword"
        mock_token.is_stop = False
        mock_token.is_punct = False
        mock_token.pos_ = "NOUN"
        mock_doc.__iter__.return_value = [mock_token]
        
        # Configure mock spaCy to return our mock objects
        mock_nlp.return_value = mock_doc
        
        tagger = Tagger()
        return tagger

def test_init():
    """Test initialization with mock spaCy."""
    with patch("spacy.load") as mock_load:
        tagger = Tagger(model="en_core_web_md")
        mock_load.assert_called_once_with("en_core_web_md")
        assert isinstance(tagger.custom_tags, set)

def test_add_custom_tags(tagger):
    """Test adding custom tags."""
    tagger.add_custom_tags(["tag1", "tag2"])
    assert "tag1" in tagger.custom_tags
    assert "tag2" in tagger.custom_tags
    
    # Add a duplicate tag
    tagger.add_custom_tags(["tag1", "tag3"])
    assert len(tagger.custom_tags) == 3

def test_generate_tags(tagger):
    """Test generating tags for a block."""
    # Add a custom tag that matches our mock keyword
    tagger.add_custom_tags(["keyword"])
    
    # Create a test block
    block = Block(id="test", type="paragraph", content="This is a test with keyword")
    
    # Generate tags
    tags = tagger.generate_tags(block)
    
    # Should have two tags: one entity and one custom
    assert len(tags) == 2
    
    # Check entity tag
    assert any(t.name == "test entity" and t.type == "entity" and t.category == "ORG" for t in tags)
    
    # Check custom tag
    assert any(t.name == "keyword" and t.type == "custom" and t.category == "keyword" for t in tags)

@pytest.mark.skip("Sentiment analysis test not implemented correctly yet")
def test_analyze_sentiment(tagger):
    """Test sentiment analysis."""
    # Mock sentiment analysis
    with patch.object(tagger, "nlp") as mock_nlp:
        # Create a mock document
        mock_doc = MagicMock()
        mock_token_pos = MagicMock()
        mock_token_pos.pos_ = "ADJ"
        mock_token_pos.is_stop = False
        
        mock_token_neg = MagicMock()
        mock_token_neg.pos_ = "ADJ"
        mock_token_neg.is_stop = True
        
        mock_doc.__iter__.return_value = [mock_token_pos, mock_token_neg]
        mock_nlp.return_value = mock_doc
        
        # Test sentiment analysis
        sentiment = tagger.analyze_sentiment("This is a test")
        
        # Check sentiment scores
        assert "positive" in sentiment
        assert "negative" in sentiment
        assert sentiment["positive"] == 0.5
        assert sentiment["negative"] == 0.5