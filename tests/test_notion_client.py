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
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": "page1",
                "created_time": "2023-01-01T00:00:00Z",
                "last_edited_time": "2023-01-02T00:00:00Z",
                "properties": {
                    "title": [{"text": {"content": "Test Page"}}]
                }
            }
        ]
    }
    
    with patch("requests.post", return_value=mock_response) as mock_post:
        documents = notion_client.list_documents()
        
        mock_post.assert_called_once()
        assert len(documents) == 1
        assert documents[0].id == "page1"
        assert documents[0].title == "Test Page"
        assert isinstance(documents[0], Document)

def test_get_document_content(notion_client):
    """Test getting document content."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
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
    
    with patch("requests.get", return_value=mock_response) as mock_get:
        blocks = notion_client.get_document_content("page1")
        
        mock_get.assert_called_once()
        assert len(blocks) == 1
        assert blocks[0].id == "block1"
        assert blocks[0].type == "paragraph"
        assert blocks[0].content == "Test content"
        assert isinstance(blocks[0], Block)