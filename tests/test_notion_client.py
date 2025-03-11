"""
Tests for the Notion client implementation.
"""
import pytest
from notion_nlp.notion_client import NotionClient
from notion_nlp.exceptions import AuthenticationError
from notion_nlp.models import Document, Block

def test_authentication():
    """Test authentication process."""
    client = NotionClient("fake_token")
    with pytest.raises(AuthenticationError):
        client.authenticate()

def test_list_documents(mocker):
    """Test listing documents."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": "test-id",
                "properties": {"title": [{"text": {"content": "Test Doc"}}]},
                "created_time": "2023-01-01T00:00:00Z",
                "last_edited_time": "2023-01-01T00:00:00Z"
            }
        ]
    }

    mocker.patch('requests.post', return_value=mock_response)

    client = NotionClient("fake_token")
    docs = client.list_documents()

    assert len(docs) == 1
    assert isinstance(docs[0], Document)
    assert docs[0].title == "Test Doc"

def test_get_document_content(mocker):
    """Test retrieving document content."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": "block-id",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Test content"},
                            "plain_text": "Test content"
                        }
                    ]
                },
                "has_children": False
            }
        ],
        "has_more": False
    }

    mocker.patch('requests.get', return_value=mock_response)

    client = NotionClient("fake_token")
    blocks = client.get_document_content("doc-id")

    assert len(blocks) == 1
    assert isinstance(blocks[0], Block)
    assert blocks[0].content == "Test content"