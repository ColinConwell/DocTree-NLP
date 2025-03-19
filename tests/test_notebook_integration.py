"""
Test the Jupyter notebook integration.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from doctree_nlp.structure import Document, Block
from doctree_nlp.notebook import (
    document_to_html, 
    display_document, 
    display_document_tree,
    document_to_table_html,
    display_document_table
)

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
        Block(id="block6", type="paragraph", content="Another paragraph.", has_children=False),
    ]
    
    return doc

def test_document_to_html(sample_document):
    """Test converting document to HTML."""
    html = document_to_html(sample_document)
    
    # Check that HTML contains document info
    assert 'class="notionlp-doc"' in html
    assert 'Test Document' in html
    assert 'doc1' in html
    assert '2023-01-01' in html
    assert '2023-01-02' in html
    
    # Check that HTML contains block previews
    assert 'heading_1' in html
    assert 'Heading 1' in html
    assert 'preview-block' in html
    assert 'more blocks' in html  # Should mention there are more blocks

def test_display_document(sample_document):
    """Test displaying document."""
    with patch('doctree_nlp.notebook.HTML') as mock_html, \
         patch('doctree_nlp.notebook.display') as mock_display:
        
        # Mock HTML function to return input
        mock_html.side_effect = lambda x: x
        
        # Call display function
        display_document(sample_document)
        
        # Check that HTML was created and displayed
        mock_html.assert_called_once()
        mock_display.assert_called_once()
        
        # Check that HTML contains document title
        html_content = mock_html.call_args[0][0]
        assert 'Test Document' in html_content

def test_display_document_tree(sample_document):
    """Test displaying document tree."""
    # Build tree first
    sample_document.build_tree()
    
    with patch('doctree_nlp.notebook.HTML') as mock_html, \
         patch('doctree_nlp.notebook.display') as mock_display:
        
        # Mock HTML function to return input
        mock_html.side_effect = lambda x: x
        
        # Call display function
        display_document_tree(sample_document)
        
        # Check that HTML was created and displayed
        mock_html.assert_called_once()
        mock_display.assert_called_once()
        
        # Check that HTML contains tree elements
        html_content = mock_html.call_args[0][0]
        assert 'tree-node' in html_content
        assert 'tree-content' in html_content
        assert 'toggle-btn' in html_content
        assert 'toggleNode' in html_content  # JavaScript function

def test_document_to_table_html(sample_document):
    """Test converting document to table HTML."""
    html = document_to_table_html(sample_document)
    
    # Check that HTML contains table structure
    assert 'class="notionlp-table"' in html
    assert '<th>#</th><th>Type</th><th>Content</th>' in html
    assert '<tbody>' in html
    
    # Check that blocks are in the table
    assert 'heading_1' in html
    assert 'Heading 1' in html
    assert 'paragraph' in html
    assert 'This is a paragraph.' in html

def test_display_document_table(sample_document):
    """Test displaying document as table."""
    with patch('doctree_nlp.notebook.HTML') as mock_html, \
         patch('doctree_nlp.notebook.display') as mock_display:
        
        # Mock HTML function to return input
        mock_html.side_effect = lambda x: x
        
        # Call display function
        display_document_table(sample_document)
        
        # Check that HTML was created and displayed
        mock_html.assert_called_once()
        mock_display.assert_called_once()
        
        # Check that HTML contains table
        html_content = mock_html.call_args[0][0]
        assert 'notionlp-table' in html_content
        assert '<th>#</th><th>Type</th><th>Content</th>' in html_content

def test_auto_build_tree_for_display(sample_document):
    """Test that tree is automatically built if needed."""
    # Don't build tree ahead of time
    sample_document.tree = None
    
    with patch('doctree_nlp.notebook.HTML') as mock_html, \
         patch('doctree_nlp.notebook.display') as mock_display:
        
        # Mock HTML function to return input
        mock_html.side_effect = lambda x: x
        
        # Call display function
        display_document_tree(sample_document)
        
        # Check that tree was built
        assert sample_document.tree is not None