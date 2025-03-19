"""
Test the NotionClient.get_document method.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from doctree_nlp.api_client import NotionClient
from doctree_nlp.structure import Document, Block

@pytest.fixture
def mock_client():
    """Return a NotionClient with mocked API calls."""
    with patch('doctree_nlp.api_client.find_notion_token', return_value="fake_token"), \
         patch('doctree_nlp.api_client.CacheManager'), \
         patch('doctree_nlp.api_client.RateLimiter'), \
         patch('doctree_nlp.api_client.requests.get'), \
         patch('doctree_nlp.api_client.requests.post'):
        client = NotionClient(token="fake_token", cache_enabled=False)
        return client

def test_get_document(mock_client):
    """Test getting a document with content."""
    # Mock document metadata and blocks
    mock_document = Document(
        id="doc1",
        title="Test Document",
        created_time=datetime(2023, 1, 1, 12, 0, 0),
        last_edited_time=datetime(2023, 1, 2, 12, 0, 0),
        last_fetched=datetime.now(),
        etag="etag123"
    )
    
    mock_blocks = [
        Block(id="block1", type="heading_1", content="Heading 1"),
        Block(id="block2", type="paragraph", content="Paragraph content")
    ]
    
    # Mock the get_document_content method
    with patch.object(mock_client, 'get_document_content', return_value=(mock_document, mock_blocks)):
        # Call get_document
        result = mock_client.get_document("doc1")
        
        # Check document properties
        assert result.id == "doc1"
        assert result.title == "Test Document"
        assert result.created_time == datetime(2023, 1, 1, 12, 0, 0)
        assert result.last_edited_time == datetime(2023, 1, 2, 12, 0, 0)
        assert result.etag == "etag123"
        
        # Check blocks
        assert len(result.blocks) == 2
        assert result.blocks[0].id == "block1"
        assert result.blocks[0].type == "heading_1"
        assert result.blocks[0].content == "Heading 1"
        assert result.blocks[1].id == "block2"
        assert result.blocks[1].type == "paragraph"
        assert result.blocks[1].content == "Paragraph content"

def test_get_document_fallback(mock_client):
    """Test getting a document when metadata fetch fails."""
    # Mock empty metadata and some blocks
    mock_blocks = [
        Block(id="block1", type="heading_1", content="Heading 1"),
        Block(id="block2", type="paragraph", content="Paragraph content")
    ]
    
    # Mock the get_document_content method to return None for metadata
    with patch.object(mock_client, 'get_document_content', return_value=(None, mock_blocks)):
        # Call get_document
        result = mock_client.get_document("doc1")
        
        # Check fallback document properties
        assert result.id == "doc1"
        assert result.title == "Unknown Document"
        
        # Check blocks were still added
        assert len(result.blocks) == 2
        assert result.blocks[0].id == "block1"
        assert result.blocks[1].id == "block2"

def test_get_document_with_cache(mock_client):
    """Test getting a document with caching."""
    # Enable cache for test
    mock_client.cache_enabled = True
    
    # Mock document and blocks
    mock_document = Document(
        id="doc1",
        title="Test Document",
        created_time=datetime(2023, 1, 1, 12, 0, 0),
        last_edited_time=datetime(2023, 1, 2, 12, 0, 0),
        last_fetched=datetime.now()
    )
    
    mock_blocks = [
        Block(id="block1", type="heading_1", content="Heading 1")
    ]
    
    # Mock the get_document_content method
    with patch.object(mock_client, 'get_document_content', return_value=(mock_document, mock_blocks)):
        # Call get_document with cache=True
        result = mock_client.get_document("doc1", use_cache=True)
        
        # Check document was returned correctly
        assert result.id == "doc1"
        assert result.title == "Test Document"
        assert len(result.blocks) == 1
        
        # Verify get_document_content was called with correct use_cache value
        mock_client.get_document_content.assert_called_once_with("doc1", True)

def test_document_tree_building(mock_client):
    """Test that a document tree can be built from the returned document."""
    # Mock document metadata and blocks
    mock_document = Document(
        id="doc1",
        title="Test Document",
        created_time=datetime(2023, 1, 1, 12, 0, 0),
        last_edited_time=datetime(2023, 1, 2, 12, 0, 0)
    )
    
    # Create a structured mock set of blocks
    mock_blocks = [
        Block(id="block1", type="heading_1", content="Heading 1"),
        Block(id="block2", type="heading_2", content="Heading 2"),
        Block(id="block3", type="paragraph", content="Paragraph 1"),
        Block(id="block4", type="heading_2", content="Heading 3"),
        Block(id="block5", type="paragraph", content="Paragraph 2")
    ]
    
    # Mock the get_document_content method
    with patch.object(mock_client, 'get_document_content', return_value=(mock_document, mock_blocks)):
        # Call get_document
        result = mock_client.get_document("doc1")
        
        # Build tree
        tree = result.build_tree()
        
        # Check tree structure
        assert tree.root is not None
        assert len(tree.root.children) == 1  # Should have one heading_1
        
        heading1 = tree.root.children[0]
        assert heading1.block.type == "heading_1"
        assert heading1.block.content == "Heading 1"
        assert len(heading1.children) == 2  # Should have two heading_2s
        
        # Check first heading_2 and its paragraph
        heading2 = heading1.children[0]
        assert heading2.block.type == "heading_2"
        assert heading2.block.content == "Heading 2"
        assert len(heading2.children) == 1
        assert heading2.children[0].block.content == "Paragraph 1"
        
        # Check second heading_2 and its paragraph
        heading3 = heading1.children[1]
        assert heading3.block.type == "heading_2"
        assert heading3.block.content == "Heading 3"
        assert len(heading3.children) == 1
        assert heading3.children[0].block.content == "Paragraph 2"