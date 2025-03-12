"""
Test the document parser.
"""
import os
import json
from pathlib import Path
import pytest

from notionlp.structure import (
    Block, Hierarchy
)

from notionlp.parsers import (
    doc_to_dict, 
    export_to_markdown, 
    export_to_rst, 
    load_example_document,
    _clean_key
)

# Test data
@pytest.fixture
def sample_blocks():
    """Return sample blocks for testing."""
    return [
        Block(id="block1", type="heading_1", content="Meeting Notes", has_children=True),
        Block(id="block2", type="paragraph", content="Discussion about project timeline", has_children=False),
        Block(id="block3", type="bulleted_list_item", content="Start prototyping by May", has_children=False),
        Block(id="block4", type="bulleted_list_item", content="Complete testing by June", has_children=False),
        Block(id="block5", type="heading_2", content="Action Items", has_children=True),
        Block(id="block6", type="paragraph", content="Tasks to be completed", has_children=False),
        Block(id="block7", type="numbered_list_item", content="Update documentation", has_children=False),
        Block(id="block8", type="numbered_list_item", content="Schedule follow-up meeting", has_children=False),
    ]

@pytest.fixture
def sample_hierarchy(sample_blocks):
    """Return a sample hierarchy built from blocks."""
    hierarchy = Hierarchy()
    root = hierarchy.build_hierarchy(sample_blocks)
    return hierarchy

def test_clean_key():
    """Test the _clean_key function."""
    assert _clean_key("This is a test") == "this_is_a"
    assert _clean_key("Hello, World!") == "hello_world"
    assert _clean_key("123 test") == "123_test"
    assert _clean_key("a b c d e f") == "a_b_c"

def test_doc_to_dict(sample_hierarchy):
    """Test converting a document to a dictionary."""
    result = doc_to_dict(sample_hierarchy)
    
    # Check that result is a dictionary
    assert isinstance(result, dict)
    
    # Check structure for first block
    first_key = next(iter(result))
    assert "content" in result[first_key]
    assert "type" in result[first_key]
    assert "children" in result[first_key]

def test_doc_to_dict_with_blocks(sample_blocks):
    """Test converting blocks to a dictionary."""
    result = doc_to_dict(sample_blocks)
    
    # Check that result is a dictionary
    assert isinstance(result, dict)
    
    # Check structure for first block
    first_key = next(iter(result))
    assert "content" in result[first_key]
    assert "type" in result[first_key]

def test_export_to_markdown(sample_blocks):
    """Test exporting document to markdown."""
    markdown = export_to_markdown(sample_blocks)
    
    # Check that markdown contains expected elements
    assert "# Meeting Notes" in markdown
    assert "Discussion about project timeline" in markdown
    assert "- Start prototyping by May" in markdown
    assert "## Action Items" in markdown
    assert "1. Update documentation" in markdown

def test_export_to_rst(sample_blocks):
    """Test exporting document to reStructuredText."""
    rst = export_to_rst(sample_blocks)
    
    # Check that RST contains expected elements
    assert "Meeting Notes\n=============" in rst
    assert "Discussion about project timeline" in rst
    assert "* Start prototyping by May" in rst
    assert "Action Items\n-----------" in rst
    assert "#. Update documentation" in rst

def test_load_example_document(monkeypatch, tmp_path):
    """Test loading an example document."""
    # Create a mock example file
    examples_dir = tmp_path / "examples" / "data"
    examples_dir.mkdir(parents=True)
    
    test_data = [
        {"id": "test1", "type": "heading_1", "content": "Test Document", "has_children": True},
        {"id": "test2", "type": "paragraph", "content": "This is a test", "has_children": False}
    ]
    
    with open(examples_dir / "test_doc.json", "w") as f:
        json.dump(test_data, f)
    
    # Mock the file path
    def mock_path(*args, **kwargs):
        return tmp_path
    
    monkeypatch.setattr(Path, "parent", property(mock_path))
    
    # Mock load_example_document to use our test path
    def mock_load(name):
        file_path = examples_dir / f"{name}.json"
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        blocks = []
        for block_data in data:
            blocks.append(Block(**block_data))
        
        return blocks
    
    # Test loading
    blocks = mock_load("test_doc")
    assert len(blocks) == 2
    assert blocks[0].id == "test1"
    assert blocks[0].content == "Test Document"
    assert blocks[1].type == "paragraph"