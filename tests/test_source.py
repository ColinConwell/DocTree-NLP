"""
Test the Source class.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from notionlp.structure import Source

@pytest.fixture
def sample_source():
    """Return a sample source for testing."""
    return Source(
        id="source1",
        name="Test Source",
        api_type="notion",
        documents=["doc1", "doc2"],
        metadata={
            "workspace_id": "workspace123",
            "user_count": 5
        },
        last_synced=datetime(2023, 1, 1, 12, 0, 0)
    )

def test_source_init():
    """Test Source initialization."""
    source = Source(id="source1", name="Test Source")
    
    # Check default values
    assert source.id == "source1"
    assert source.name == "Test Source"
    assert source.api_type == "notion"
    assert source.documents == []
    assert source.metadata == {}
    assert source.last_synced is None

def test_source_with_values(sample_source):
    """Test Source with specified values."""
    # Check all values
    assert sample_source.id == "source1"
    assert sample_source.name == "Test Source"
    assert sample_source.api_type == "notion"
    assert sample_source.documents == ["doc1", "doc2"]
    assert sample_source.metadata == {"workspace_id": "workspace123", "user_count": 5}
    assert sample_source.last_synced == datetime(2023, 1, 1, 12, 0, 0)

def test_add_document(sample_source):
    """Test adding a document to a source."""
    # Add new document
    sample_source.add_document("doc3")
    assert "doc3" in sample_source.documents
    assert len(sample_source.documents) == 3
    
    # Try adding existing document
    sample_source.add_document("doc1")
    assert sample_source.documents.count("doc1") == 1  # Should not be added twice
    assert len(sample_source.documents) == 3

def test_to_dataframe(sample_source):
    """Test converting source metadata to DataFrame."""
    # Mock pandas
    with patch("pandas.DataFrame") as mock_df:
        mock_df.return_value = "dataframe"
        
        # Convert to dataframe
        df = sample_source.to_dataframe()
        
        # Check that pandas was called
        mock_df.assert_called_once_with(sample_source.metadata)
        assert df == "dataframe"

def test_to_dataframe_no_pandas(sample_source):
    """Test to_dataframe when pandas is not available."""
    # Mock import error
    with patch("notionlp.structure.pd", None):
        with patch("notionlp.structure.logger") as mock_logger:
            # Try to convert to dataframe
            df = sample_source.to_dataframe()
            
            # Check that warning was logged
            mock_logger.warning.assert_called_once()
            assert "pandas not installed" in mock_logger.warning.call_args[0][0]
            assert df is None