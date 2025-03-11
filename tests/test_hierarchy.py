"""
Tests for the document hierarchy implementation.
"""
import pytest
from notion_nlp.hierarchy import DocumentHierarchy, Node
from notion_nlp.models import Block

@pytest.fixture
def hierarchy():
    """Create a document hierarchy instance."""
    return DocumentHierarchy()

def test_build_hierarchy(hierarchy):
    """Test building document hierarchy."""
    blocks = [
        Block(id="1", type="heading_1", content="Title", has_children=False),
        Block(id="2", type="heading_2", content="Subtitle", has_children=False),
        Block(id="3", type="paragraph", content="Content", has_children=False)
    ]
    
    root = hierarchy.build_hierarchy(blocks)
    
    assert isinstance(root, Node)
    assert len(root.children) == 1  # heading_1
    assert len(root.children[0].children) == 1  # heading_2
    assert len(root.children[0].children[0].children) == 1  # paragraph

def test_to_dict(hierarchy):
    """Test converting hierarchy to dictionary."""
    blocks = [
        Block(id="1", type="heading_1", content="Title", has_children=False),
        Block(id="2", type="paragraph", content="Content", has_children=False)
    ]
    
    hierarchy.build_hierarchy(blocks)
    result = hierarchy.to_dict()
    
    assert isinstance(result, dict)
    assert "children" in result
    assert len(result["children"]) == 1
