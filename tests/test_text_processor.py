"""
Tests for the text processor implementation.
"""
import pytest
from notion_nlp.text_processor import TextProcessor
from notion_nlp.models import Block

@pytest.fixture
def processor():
    """Create a text processor instance."""
    return TextProcessor()

def test_process_blocks(processor):
    """Test processing text blocks."""
    blocks = [
        Block(
            id="1",
            type="paragraph",
            content="John works at Apple in California.",
            has_children=False
        )
    ]
    
    processed = processor.process_blocks(blocks)
    
    assert len(processed) == 1
    assert "entities" in processed[0]
    assert "sentences" in processed[0]
    assert "keywords" in processed[0]

def test_extract_summary(processor):
    """Test text summarization."""
    text = """
    The quick brown fox jumps over the lazy dog.
    This is a second sentence about something else.
    And here is a third sentence with different content.
    Finally, this is the fourth sentence of the text.
    """
    
    summary = processor.extract_summary(text, sentences=2)
    
    assert isinstance(summary, str)
    assert len(summary.split('.')) <= 3
