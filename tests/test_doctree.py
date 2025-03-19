"""
Test the DocTree class.
"""
import pytest
from doctree_nlp.structure import DocTree, Block, Node

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

def test_build_tree(sample_blocks):
    """Test building tree from blocks."""
    tree = DocTree()
    root = tree.build_tree(sample_blocks)

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
    """Test converting tree to dictionary."""
    tree = DocTree()
    root = tree.build_tree(sample_blocks)
    
    # Convert to dict
    result = tree.to_dict()
    
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

def test_find_node_by_id(sample_blocks):
    """Test finding a node by ID."""
    tree = DocTree()
    tree.build_tree(sample_blocks)
    
    # Find node
    node = tree.find_node_by_id("block3")
    assert node is not None
    assert node.block.id == "block3"
    assert node.block.content == "Paragraph 1"
    
    # Try finding non-existent node
    node = tree.find_node_by_id("non_existent")
    assert node is None

def test_find_nodes_by_type(sample_blocks):
    """Test finding nodes by type."""
    tree = DocTree()
    tree.build_tree(sample_blocks)
    
    # Find nodes by type
    nodes = tree.find_nodes_by_type("paragraph")
    assert len(nodes) == 3
    
    # Check content of found nodes
    contents = sorted([node.block.content for node in nodes])
    assert contents == ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
    
    # Try finding nodes of a type that doesn't exist
    nodes = tree.find_nodes_by_type("non_existent_type")
    assert len(nodes) == 0

def test_find_nodes_by_content(sample_blocks):
    """Test finding nodes by content pattern."""
    tree = DocTree()
    tree.build_tree(sample_blocks)
    
    # Find nodes by content pattern
    nodes = tree.find_nodes_by_content("Paragraph")
    assert len(nodes) == 3
    
    # Find nodes with more specific pattern
    nodes = tree.find_nodes_by_content("Paragraph 1")
    assert len(nodes) == 1
    assert nodes[0].block.content == "Paragraph 1"
    
    # Try finding nodes with non-existent content
    nodes = tree.find_nodes_by_content("Non-existent Content")
    assert len(nodes) == 0