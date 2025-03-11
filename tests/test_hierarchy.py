"""
Test the hierarchy module.
"""
import pytest

from notion_nlp.core import Hierarchy, Node, Block

@pytest.fixture
def sample_blocks():
    """Return sample blocks for testing."""
    return [
        Block(id="block1", type="heading_1", content="Heading 1", has_children=False),
        Block(id="block2", type="heading_2", content="Heading 2", has_children=False),
        Block(id="block3", type="paragraph", content="Paragraph 1", has_children=False),
        Block(id="block4", type="paragraph", content="Paragraph 2", has_children=False),
        Block(id="block5", type="heading_2", content="Heading 3", has_children=False),
        Block(id="block6", type="paragraph", content="Paragraph 3", has_children=False),
    ]

def test_build_hierarchy(sample_blocks):
    """Test building hierarchy from blocks."""
    hierarchy = Hierarchy()
    root = hierarchy.build_hierarchy(sample_blocks)

    # Check that root was created properly
    assert root.block.id == "root"
    assert root.block.type == "root"
    assert len(root.children) == 1  # Should have one top-level heading

    # Check first heading
    heading1 = root.children[0]
    assert heading1.block.content == "Heading 1"
    assert len(heading1.children) == 2  # Should have two sub-headings

    # Check first sub-heading
    heading2 = heading1.children[0]
    assert heading2.block.content == "Heading 2"
    assert len(heading2.children) == 2  # Should have two paragraphs

    # Check paragraphs under first sub-heading
    assert heading2.children[0].block.content == "Paragraph 1"
    assert heading2.children[1].block.content == "Paragraph 2"

    # Check second sub-heading
    heading3 = heading1.children[1]
    assert heading3.block.content == "Heading 3"
    assert len(heading3.children) == 1  # Should have one paragraph

    # Check paragraph under second sub-heading
    assert heading3.children[0].block.content == "Paragraph 3"

def test_to_dict(sample_blocks):
    """Test converting hierarchy to dictionary."""
    hierarchy = Hierarchy()
    root = hierarchy.build_hierarchy(sample_blocks)
    
    # Convert to dict
    result = hierarchy.to_dict()
    
    # Check structure
    assert result["id"] == "root"
    assert result["type"] == "root"
    assert result["content"] == ""
    assert len(result["children"]) == 1
    
    # Check first child
    first_child = result["children"][0]
    assert first_child["id"] == "block1"
    assert first_child["content"] == "Heading 1"
    assert len(first_child["children"]) == 2