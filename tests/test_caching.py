"""
Test the cache manager functionality.
"""
import pytest
import tempfile
import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta

from doctree_nlp.caching import CacheManager
from doctree_nlp.structure import Document, Block

@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for testing cache."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def document():
    """Create a test document."""
    return Document(
        id="test-doc-id",
        title="Test Document",
        created_time=datetime(2023, 1, 1),
        last_edited_time=datetime(2023, 1, 2),
        last_fetched=datetime.now()
    )

@pytest.fixture
def blocks():
    """Create test blocks."""
    return [
        Block(
            id="block1",
            type="heading_1",
            content="Heading 1",
            has_children=False
        ),
        Block(
            id="block2",
            type="paragraph",
            content="Paragraph text",
            has_children=False
        )
    ]

def test_cache_manager_api_specific(temp_cache_dir):
    """Test that cache manager creates different caches for different API tokens."""
    # Create two cache managers with different tokens
    cache1 = CacheManager(api_token="token1", cache_dir=temp_cache_dir)
    cache2 = CacheManager(api_token="token2", cache_dir=temp_cache_dir)
    
    # Check that they use different subdirectories
    assert cache1.cache_dir != cache2.cache_dir
    assert cache1.cache_dir.parent == cache2.cache_dir.parent
    assert cache1.cache_dir.parent.parent == Path(temp_cache_dir)
    
    # Verify both directories were created
    assert cache1.cache_dir.exists()
    assert cache2.cache_dir.exists()

def test_cache_last_edited_check(temp_cache_dir, document, blocks):
    """Test that cache checks document edit time to determine if cache is valid."""
    # Create cache manager
    cache = CacheManager(api_token="test_token", cache_dir=temp_cache_dir)
    
    # Cache a document
    cache.cache_document("test-doc", document, blocks)
    
    # Check that document is cached
    assert cache.is_document_cached("test-doc")
    
    # Check with older edit time (should use cache)
    older_time = datetime(2023, 1, 1)
    assert cache.is_document_cached("test-doc", older_time)
    
    # Check with newer edit time (should invalidate cache)
    newer_time = datetime(2023, 1, 3)
    assert not cache.is_document_cached("test-doc", newer_time)

def test_cache_max_age(temp_cache_dir, document, blocks):
    """Test that max_age setting works correctly."""
    # Create cache manager with a short max age of 1 second
    cache = CacheManager(api_token="test_token", cache_dir=temp_cache_dir, max_age_days=1/86400)  # 1 second
    
    # Cache a document
    cache.cache_document("test-doc", document, blocks)
    
    # Check immediately (should be cached)
    assert cache.is_document_cached("test-doc")
    
    # Sleep for 2 seconds to let cache expire
    import time
    time.sleep(2)
    
    # Check again (should now be expired)
    assert not cache.is_document_cached("test-doc")

def test_no_max_age(temp_cache_dir, document, blocks):
    """Test that setting max_age to None disables time-based expiration."""
    # Create cache manager with no max age
    cache = CacheManager(api_token="test_token", cache_dir=temp_cache_dir, max_age_days=None)
    
    # Cache a document
    cache.cache_document("test-doc", document, blocks)
    
    # Check that max_age_seconds is None
    assert cache.max_age_seconds is None
    
    # Check immediately (should be cached)
    assert cache.is_document_cached("test-doc")
    
    # Sleep for 2 seconds
    import time
    time.sleep(2)
    
    # Check again (should still be cached since there's no expiration)
    assert cache.is_document_cached("test-doc")
    
    # Check that the only way to invalidate is with a newer edited time
    newer_time = document.last_edited_time + timedelta(seconds=1)
    assert not cache.is_document_cached("test-doc", newer_time)