"""
Test the Notion client module.
"""
import pytest
from unittest.mock import MagicMock, patch

from notionlp.api_client import (
    NotionClient, AuthenticationError
)

from notionlp.structure import Document, Block

@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = MagicMock()
    response.status_code = 200
    return response

@pytest.fixture
def notion_client():
    """Return a NotionClient instance with a test token."""
    return NotionClient("test_token")

def test_init():
    """Test initialization."""
    client = NotionClient("test_token")
    assert client.token == "test_token"
    assert "Bearer test_token" in client.headers["Authorization"]
    assert client.headers["Notion-Version"] == "2022-06-28"
    
def test_api_specific_cache():
    """Test that different API tokens use different cache directories."""
    client1 = NotionClient("token1")
    client2 = NotionClient("token2")
    
    # Check that cache managers use different directories
    assert client1.cache_manager.cache_dir != client2.cache_manager.cache_dir
    
    # Verify that max_age_days is None by default (no expiry)
    assert client1.cache_manager.max_age_seconds is None

def test_authenticate_success(notion_client, mock_response):
    """Test successful authentication."""
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = notion_client.authenticate()
        
        mock_get.assert_called_once()
        assert "users/me" in mock_get.call_args[0][0]
        assert result is True

def test_authenticate_failure(notion_client):
    """Test authentication failure."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    
    with patch("requests.get", return_value=mock_response) as mock_get:
        with pytest.raises(AuthenticationError):
            notion_client.authenticate()

def test_list_documents(notion_client):
    """Test listing documents."""
    # Create mock response for the API call
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": "page1",
                "created_time": "2023-01-01T00:00:00Z",
                "last_edited_time": "2023-01-02T00:00:00Z",
                "properties": {
                    "title": {"title": [{"text": {"content": "Test Page"}}]}
                }
            }
        ]
    }
    
    # Mock the cache check to return None (forcing API call)
    with patch.object(notion_client, 'cache_manager', None):
        # Apply patch to requests.post
        with patch("requests.post", return_value=mock_response) as mock_post:
            # Call the method under test with cache disabled
            documents = notion_client.list_documents(use_cache=False)
            
            # Verify the POST request was made with correct parameters
            mock_post.assert_called_once()
            assert "/search" in mock_post.call_args[0][0]
            
            # Verify the response was processed correctly
            assert len(documents) == 1
            assert documents[0].id == "page1"
            assert documents[0].title == "Test Page"
            assert isinstance(documents[0], Document)

def test_get_document_content(notion_client):
    """Test getting document content."""
    # Mock response for document metadata
    mock_metadata_response = MagicMock()
    mock_metadata_response.status_code = 200
    mock_metadata_response.json.return_value = {
        "id": "page1",
        "created_time": "2023-01-01T00:00:00Z",
        "last_edited_time": "2023-01-02T00:00:00Z",
        "properties": {
            "title": [{"text": {"content": "Test Page"}}]
        }
    }
    
    # Mock response for document content
    mock_content_response = MagicMock()
    mock_content_response.status_code = 200
    mock_content_response.json.return_value = {
        "results": [
            {
                "id": "block1",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"plain_text": "Test content"}]
                },
                "has_children": False
            }
        ],
        "has_more": False
    }
    
    # Apply patches to handle both API calls
    with patch("requests.get") as mock_get:
        # Configure the mock to return different responses based on the URL
        def side_effect(url, **kwargs):
            if "/pages/" in url:
                return mock_metadata_response
            elif "/blocks/" in url:
                return mock_content_response
            return MagicMock(status_code=404)
            
        mock_get.side_effect = side_effect
        
        # Call the method under test
<<<<<<< HEAD
        metadata, blocks = notion_client.get_document_content("page1")
        
        # Verify results
        assert metadata.id == "page1"
        assert metadata.title == "Test Page"
        assert isinstance(metadata, Document)
=======
        document, blocks = notion_client.get_document_content("page1")
        
        # Verify results
        assert document.id == "page1"
        assert document.title == "Test Page"
        assert isinstance(document, Document)
>>>>>>> origin/main
        
        assert len(blocks) == 1
        assert blocks[0].id == "block1"
        assert blocks[0].type == "paragraph"
        assert blocks[0].content == "Test content"
        assert isinstance(blocks[0], Block)