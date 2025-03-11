"""
Test the text processor module.
"""
import pytest
from unittest.mock import MagicMock, patch

from notion_nlp.text_processor import TextProcessor
from notion_nlp.core import Block

@pytest.fixture
def text_processor():
    """Return a TextProcessor instance."""
    with patch("spacy.load") as mock_load:
        # Create a mock spaCy model
        mock_nlp = MagicMock()
        mock_load.return_value = mock_nlp
        
        # Mock spaCy output
        mock_doc = MagicMock()
        
        # Mock entities
        mock_ent = MagicMock()
        mock_ent.text = "test entity"
        mock_ent.label_ = "ORG"
        mock_ent.start_char = 0
        mock_ent.end_char = 11
        mock_doc.ents = [mock_ent]
        
        # Mock sentences
        mock_sent = MagicMock()
        mock_sent.__str__.return_value = "Test sentence."
        mock_doc.sents = [mock_sent]
        
        # Mock tokens
        mock_token = MagicMock()
        mock_token.text = "keyword"
        mock_token.is_stop = False
        mock_token.is_punct = False
        mock_token.pos_ = "NOUN"
        mock_doc.__iter__.return_value = [mock_token]
        
        # Configure mock spaCy to return our mock objects
        mock_nlp.return_value = mock_doc
        
        processor = TextProcessor()
        return processor

def test_init():
    """Test initialization with mock spaCy."""
    with patch("spacy.load") as mock_load:
        processor = TextProcessor(model="en_core_web_md")
        mock_load.assert_called_once_with("en_core_web_md")

def test_process_blocks(text_processor):
    """Test processing blocks with NLP pipeline."""
    # Create test blocks
    blocks = [
        Block(id="block1", type="paragraph", content="This is a test paragraph."),
        Block(id="block2", type="heading_1", content="This is a heading.")
    ]
    
    # Process blocks
    processed = text_processor.process_blocks(blocks)
    
    # Check results
    assert len(processed) == 2
    
    # Check first block processing
    assert processed[0]["id"] == "block1"
    assert processed[0]["type"] == "paragraph"
    assert processed[0]["content"] == "This is a test paragraph."
    
    # Check NLP annotations
    assert len(processed[0]["entities"]) == 1
    assert processed[0]["entities"][0]["text"] == "test entity"
    assert processed[0]["entities"][0]["label"] == "ORG"
    
    assert len(processed[0]["sentences"]) == 1
    assert processed[0]["sentences"][0] == "Test sentence."
    
    assert len(processed[0]["keywords"]) == 1
    assert processed[0]["keywords"][0] == "keyword"

def test_extract_summary(text_processor):
    """Test extracting summary from text."""
    with patch.object(text_processor, "nlp") as mock_nlp:
        # Mock sentencizer
        mock_doc = MagicMock()
        
        # Mock sentences with scores
        mock_sent1 = MagicMock()
        mock_sent1.text = "This is the first sentence."
        
        mock_sent2 = MagicMock()
        mock_sent2.text = "This is the second sentence with more tokens."
        
        mock_sent3 = MagicMock()
        mock_sent3.text = "This is the third sentence."
        
        # Mock tokens for sentences
        mock_token_stop = MagicMock()
        mock_token_stop.is_stop = True
        mock_token_stop.is_punct = False
        
        mock_token_content = MagicMock()
        mock_token_content.is_stop = False
        mock_token_content.is_punct = False
        
        # First sentence: 1 content token
        mock_sent1.__iter__.return_value = [mock_token_stop, mock_token_content]
        
        # Second sentence: 3 content tokens
        mock_sent2.__iter__.return_value = [mock_token_content, mock_token_content, mock_token_content]
        
        # Third sentence: 2 content tokens
        mock_sent3.__iter__.return_value = [mock_token_content, mock_token_content]
        
        mock_doc.sents = [mock_sent1, mock_sent2, mock_sent3]
        mock_nlp.return_value = mock_doc
        
        # Test summary extraction (default: 3 sentences)
        summary = text_processor.extract_summary("Test text")
        
        # Should contain all three sentences, ordered by importance
        assert "second sentence" in summary  # Most important (3 tokens)
        assert "third sentence" in summary  # Second most important (2 tokens)
        assert "first sentence" in summary  # Least important (1 token)
        
        # Test with fewer sentences
        summary = text_processor.extract_summary("Test text", sentences=2)
        
        # Should only have top 2 sentences
        assert len(summary.split("This is the")) == 3  # "This is the" appears twice, plus text before