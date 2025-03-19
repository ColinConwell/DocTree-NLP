"""
Test the Document class.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from notionlp.structure import Document, Block, DocTree

@pytest.fixture
def sample_document():
    """Return a sample document for testing."""
    doc = Document(
        id="doc1",
        title="Test Document",
        created_time=datetime(2023, 1, 1, 12, 0, 0),
        last_edited_time=datetime(2023, 1, 2, 12, 0, 0),
    )
    
    # Add blocks
    doc.blocks = [
        Block(id="block1", type="heading_1", content="Heading 1", has_children=False),
        Block(id="block2", type="heading_2", content="Heading 2", has_children=False),
        Block(id="block3", type="paragraph", content="This is a paragraph.", has_children=False),
        Block(id="block4", type="bulleted_list_item", content="Bullet point 1", has_children=False),
        Block(id="block5", type="numbered_list_item", content="Numbered item 1", has_children=False),
    ]
    
    return doc

def test_build_tree(sample_document):
    """Test building a document tree."""
    # Build tree
    tree = sample_document.build_tree()
    
    # Check that tree was created properly
    assert tree is not None
    assert tree.root is not None
    assert tree.root.block.type == "root"
    
    # Check document's tree attribute
    assert sample_document.tree is tree
    
    # Check tree structure
    heading1 = tree.root.children[0]
    assert heading1.block.content == "Heading 1"
    assert heading1.block.type == "heading_1"

def test_to_dict(sample_document):
    """Test converting document to dictionary."""
    # Build tree first
    sample_document.build_tree()
    
    # Convert to dict
    result = sample_document.to_dict()
    
    # Check basic properties
    assert result["id"] == "doc1"
    assert result["title"] == "Test Document"
    assert result["created_time"] == "2023-01-01T12:00:00"
    assert result["last_edited_time"] == "2023-01-02T12:00:00"
    
    # Check that content was included
    assert "content" in result

def test_to_markdown(sample_document):
    """Test converting document to Markdown."""
    # Convert to markdown
    markdown = sample_document.to_markdown()
    
    # Check content
    assert "# Heading 1" in markdown
    assert "## Heading 2" in markdown
    assert "This is a paragraph." in markdown
    assert "- Bullet point 1" in markdown
    assert "1. Numbered item 1" in markdown

def test_to_rst(sample_document):
    """Test converting document to RST."""
    # Convert to RST
    rst = sample_document.to_rst()
    
    # Check content
    assert "Heading 1\n=========" in rst
    assert "Heading 2\n---------" in rst
    assert "This is a paragraph." in rst
    assert "* Bullet point 1" in rst
    assert "#. Numbered item 1" in rst

def test_preview_blocks(sample_document):
    """Test previewing document blocks."""
    # Preview with default settings
    preview = sample_document.preview_blocks()
    assert len(preview) == 5
    
    # Preview with custom limit
    preview = sample_document.preview_blocks(n=2)
    assert len(preview) == 2
    assert preview[0].content == "Heading 1"
    assert preview[1].content == "Heading 2"

def test_preview_text(sample_document):
    """Test previewing document text."""
    # Preview with default settings
    preview = sample_document.preview_text()
    assert "Heading 1" in preview
    assert "Heading 2" in preview
    assert "This is a paragraph." in preview
    
    # Preview with custom limit
    preview = sample_document.preview_text(n_chars=15)
    assert len(preview) == 18  # 15 chars plus "..."
    assert preview.endswith("...")

def test_preview_sentences(sample_document):
    """Test previewing document sentences."""
    # Preview with default settings
    preview = sample_document.preview_sentences()
    assert "Heading 1" in preview
    assert "Heading 2" in preview
    assert "This is a paragraph." in preview
    
    # Preview with custom limit
    # Create a test sample with more sentences
    test_doc = Document(
        id="test",
        title="Test",
        created_time=datetime(2023, 1, 1),
        last_edited_time=datetime(2023, 1, 1),
        blocks=[
            Block(id="1", type="paragraph", content="Sentence one."),
            Block(id="2", type="paragraph", content="Sentence two."),
            Block(id="3", type="paragraph", content="Sentence three."),
            Block(id="4", type="paragraph", content="Sentence four."),
            Block(id="5", type="paragraph", content="Sentence five.")
        ]
    )
    preview = test_doc.preview_sentences(n=2)
    assert "Sentence one" in preview
    assert "Sentence two" in preview
    assert "..." in preview

def test_load_example():
    """Test loading an example document."""
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", create=True), \
         patch("json.load") as mock_json_load:
        
        # Set up sample data
        sample_data = {
            "id": "example_id",
            "title": "Example Document",
            "created_time": "2023-01-01T12:00:00",
            "last_edited_time": "2023-01-02T12:00:00",
            "blocks": [
                {
                    "id": "block1",
                    "type": "heading_1",
                    "content": "Example Heading",
                    "has_children": False
                },
                {
                    "id": "block2",
                    "type": "paragraph",
                    "content": "Example paragraph.",
                    "has_children": False
                }
            ]
        }
        
        # Mock json.load to return our sample data
        mock_json_load.return_value = sample_data
        
        # Call the method we're testing
        doc = Document.load_example("example")
        
        # Verify the results
        assert doc.id == "example_id"
        assert doc.title == "Example Document"
        assert doc.created_time == datetime(2023, 1, 1, 12, 0, 0)
        assert doc.last_edited_time == datetime(2023, 1, 2, 12, 0, 0)
        assert len(doc.blocks) == 2
        assert doc.blocks[0].type == "heading_1"
        assert doc.blocks[0].content == "Example Heading"
        assert doc.blocks[1].type == "paragraph"
        assert doc.blocks[1].content == "Example paragraph."