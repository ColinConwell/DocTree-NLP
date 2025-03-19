"""
Test the environment loader and auto-token functionality.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from doctree_nlp.env_loader import (
    find_notion_token,
    _is_jupyter_notebook,
    _is_script,
    _load_dotenv_file,
    _search_env_files,
    EnvLoader,
    get_env,
    get_api_key
)
from doctree_nlp.api_client import NotionClient, AuthenticationError

@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file with a token."""
    env_file = tmp_path / ".env"
    with open(env_file, "w") as f:
        f.write('NOTION_API_TOKEN="test-token-from-env-file"\n')
    return env_file

def test_load_dotenv_file(temp_env_file):
    """Test loading variables from .env file."""
    env_vars = _load_dotenv_file(temp_env_file)
    assert "NOTION_API_TOKEN" in env_vars
    assert env_vars["NOTION_API_TOKEN"] == "test-token-from-env-file"

@patch("doctree_nlp.env_loader._load_dotenv_file")
def test_search_env_files(mock_load_dotenv):
    """Test searching for .env files in directories."""
    # Mock the _load_dotenv_file function to return different values for different paths
    def side_effect(path):
        if str(path).endswith(".env"):
            return {"NOTION_API_TOKEN": "test-token-from-env"}
        elif str(path).endswith(".env.local"):
            return {"NOTION_TOKEN": "test-token-from-env-local"}
        return {}
    
    mock_load_dotenv.side_effect = side_effect
    
    # Test searching
    env_vars = _search_env_files(max_depth=1)
    
    # Should combine all found variables
    assert "NOTION_API_TOKEN" in env_vars
    assert "NOTION_TOKEN" in env_vars
    assert env_vars["NOTION_API_TOKEN"] == "test-token-from-env"
    assert env_vars["NOTION_TOKEN"] == "test-token-from-env-local"
    
    # Check that the function searched in different directories
    assert mock_load_dotenv.call_count >= 4  # At least current dir .env and variants

@patch("os.environ", {"NOTION_API_TOKEN": "test-token-from-env"})
def test_find_notion_token_from_env():
    """Test finding token from environment variables."""
    token = find_notion_token()
    assert token == "test-token-from-env"

@patch("os.environ", {})
@patch("doctree_nlp.env_loader._search_env_files")
def test_find_notion_token_from_env_file(mock_search_env_files):
    """Test finding token from .env files."""
    mock_search_env_files.return_value = {"NOTION_API_TOKEN": "test-token-from-env-file"}
    token = find_notion_token()
    assert token == "test-token-from-env-file"

@patch("os.environ", {})
@patch("doctree_nlp.env_loader._search_env_files")
@patch("doctree_nlp.env_loader._is_jupyter_notebook")
@patch("doctree_nlp.env_loader._get_jupyter_input")
def test_find_notion_token_from_jupyter(mock_get_jupyter_input, mock_is_jupyter, mock_search_env_files):
    """Test finding token from Jupyter notebook input."""
    mock_search_env_files.return_value = {}
    mock_is_jupyter.return_value = True
    mock_get_jupyter_input.return_value = "test-token-from-jupyter"
    
    token = find_notion_token()
    assert token == "test-token-from-jupyter"
    assert mock_get_jupyter_input.called

@patch("os.environ", {})
@patch("doctree_nlp.env_loader._search_env_files")
@patch("doctree_nlp.env_loader._is_jupyter_notebook")
@patch("doctree_nlp.env_loader._is_script")
@patch("doctree_nlp.env_loader._get_console_input")
def test_find_notion_token_from_console(mock_get_console_input, mock_is_script, mock_is_jupyter, mock_search_env_files):
    """Test finding token from console input."""
    mock_search_env_files.return_value = {}
    mock_is_jupyter.return_value = False
    mock_is_script.return_value = True
    mock_get_console_input.return_value = "test-token-from-console"
    
    token = find_notion_token()
    assert token == "test-token-from-console"
    assert mock_get_console_input.called

@patch("doctree_nlp.api_client.find_notion_token")
def test_notion_client_auto_token(mock_find_token):
    """Test NotionClient with auto token discovery."""
    mock_find_token.return_value = "test-token-auto"
    
    client = NotionClient(token="auto")
    assert client.token == "test-token-auto"
    assert mock_find_token.called

@patch("doctree_nlp.api_client.find_notion_token")
def test_notion_client_auto_token_not_found(mock_find_token):
    """Test NotionClient with auto token discovery when no token found."""
    mock_find_token.return_value = None
    
    with pytest.raises(AuthenticationError):
        client = NotionClient(token="auto")

def test_notion_client_explicit_token():
    """Test NotionClient with explicit token."""
    client = NotionClient(token="explicit-test-token")
    assert client.token == "explicit-test-token"
    
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])