"""
Test the get_all_available_data function of the NotionClient class.
"""

import os
import json
import pytest
from unittest.mock import patch, Mock
from datetime import datetime

from doctree_nlp.api_client import NotionClient
from doctree_nlp.caching import CacheManager

# Sample test data
SAMPLE_PAGE_DATA = {
    "id": "test-page-id",
    "object": "page",
    "created_time": "2023-01-01T00:00:00.000Z",
    "last_edited_time": "2023-01-02T00:00:00.000Z",
    "properties": {"title": {"title": [{"text": {"content": "Test Page"}}]}},
}

SAMPLE_BLOCK_DATA = [
    {
        "id": "block-1",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "plain_text": "This is a test paragraph",
                    "text": {"content": "This is a test paragraph"},
                }
            ]
        },
        "has_children": False,
    },
    {
        "id": "block-2",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [
                {"plain_text": "Test Heading", "text": {"content": "Test Heading"}}
            ]
        },
        "has_children": False,
    },
]

SAMPLE_COMMENTS_DATA = [
    {
        "id": "comment-1",
        "rich_text": [
            {"plain_text": "Test comment", "text": {"content": "Test comment"}}
        ],
    }
]


@pytest.fixture
def mock_client():
    """Create a mock NotionClient with mocked requests."""
    with patch("doctree_nlp.api_client.requests") as mock_requests:
        # Mock page response
        mock_page_response = Mock()
        mock_page_response.status_code = 200
        mock_page_response.json.return_value = SAMPLE_PAGE_DATA

        # Mock blocks response
        mock_blocks_response = Mock()
        mock_blocks_response.status_code = 200
        mock_blocks_response.json.return_value = {
            "results": SAMPLE_BLOCK_DATA,
            "has_more": False,
        }

        # Mock comments response
        mock_comments_response = Mock()
        mock_comments_response.status_code = 200
        mock_comments_response.json.return_value = {"results": SAMPLE_COMMENTS_DATA}

        # Set up request responses
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "/pages/" in url:
                return mock_page_response
            elif "/blocks/" in url and "/children" in url:
                return mock_blocks_response
            elif "/comments" in url:
                return mock_comments_response
            return Mock(status_code=404)

        mock_requests.get.side_effect = side_effect

        # Create client with mocked responses
        client = NotionClient(token="test-token", cache_enabled=False)
        yield client


def test_get_all_available_data_structure(mock_client):
    """Test that get_all_available_data returns the expected structure."""
    document_id = "test-page-id"
    raw_data = mock_client.get_all_available_data(document_id)

    # Check main sections exist
    assert "page_data" in raw_data
    assert "block_data" in raw_data
    assert "comments_data" in raw_data
    assert "_meta" in raw_data

    # Check metadata
    assert raw_data["_meta"]["document_id"] == document_id
    assert "fetched_at" in raw_data["_meta"]
    assert "api_version" in raw_data["_meta"]

    # Check page data
    assert raw_data["page_data"] == SAMPLE_PAGE_DATA

    # Check block data
    assert raw_data["block_data"] == SAMPLE_BLOCK_DATA


@patch("doctree_nlp.api_client.requests.get")
def test_get_all_available_data_error_handling(mock_get, mock_client):
    """Test error handling in get_all_available_data."""
    # Mock an error response for page data
    mock_error_response = Mock()
    mock_error_response.status_code = 404
    mock_error_response.text = "Not found"
    mock_get.return_value = mock_error_response

    document_id = "test-page-id"
    raw_data = mock_client.get_all_available_data(document_id)

    # Check that errors section is populated
    assert "errors" in raw_data
    assert "page_data" in raw_data["errors"]

    # Check that page_data is empty
    assert raw_data["page_data"] == {}


@patch("doctree_nlp.cache_manager.CacheManager.get_cached_data")
@patch("doctree_nlp.cache_manager.CacheManager.cache_raw_data")
def test_get_all_available_data_caching(
    mock_cache_raw_data, mock_get_cached_data, mock_client
):
    """Test caching functionality of get_all_available_data."""
    # Enable caching on the mock client
    mock_client.cache_enabled = True
    mock_client.cache_manager = CacheManager(api_token="test-token")

    # First call - no cache hit
    mock_get_cached_data.return_value = None
    document_id = "test-page-id"

    mock_client.get_all_available_data(document_id)

    # Verify cache was checked
    mock_get_cached_data.assert_called_once_with(f"{document_id}_raw")

    # Verify data was cached
    assert mock_cache_raw_data.called

    # Second call - with cache hit
    mock_get_cached_data.reset_mock()
    mock_cache_raw_data.reset_mock()

    # Mock a cache hit
    mock_cached_data = {
        "page_data": SAMPLE_PAGE_DATA,
        "block_data": SAMPLE_BLOCK_DATA,
        "_meta": {"cached": True},
    }
    mock_get_cached_data.return_value = mock_cached_data

    result = mock_client.get_all_available_data(document_id)

    # Verify cache was checked
    mock_get_cached_data.assert_called_once_with(f"{document_id}_raw")

    # Verify API was not called (cache_raw_data should not be called)
    assert not mock_cache_raw_data.called

    # Verify returned data is from cache
    assert result == mock_cached_data


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
