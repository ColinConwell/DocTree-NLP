"""
Tests for the lazy loading document implementation.
"""

import unittest
import logging
from unittest.mock import MagicMock, patch
from datetime import datetime

from doctree_nlp.lazy_document import LazyDocument, LazyDocumentCollection, create_lazy_document
from doctree_nlp.structure import Document, Block, DocTree
from doctree_nlp.api_client import NotionClient

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class TestLazyDocument(unittest.TestCase):
    """Test suite for LazyDocument class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock(spec=NotionClient)
        
        # Prepare some test data
        self.test_blocks = [
            Block(id="b1", type="paragraph", content="Test content 1"),
            Block(id="b2", type="heading_1", content="Test heading"),
            Block(id="b3", type="paragraph", content="Test content 2"),
            Block(id="b4", type="bulleted_list_item", content="List item 1"),
            Block(id="b5", type="bulleted_list_item", content="List item 2")
        ]
        
        self.test_document = Document(
            id="doc_123",
            title="Test Document",
            created_time=datetime.now(),
            last_edited_time=datetime.now(),
            blocks=self.test_blocks
        )
        
        # Set up mock return values
        self.mock_client.get_document_content.return_value = (self.test_document, self.test_blocks)
        
        # Create a lazy document for testing
        self.lazy_document = LazyDocument(
            id="doc_123",
            title="Test Document",
            created_time=datetime.now(),
            last_edited_time=datetime.now(),
            client=self.mock_client
        )
    
    def test_lazy_loading_blocks(self):
        """Test that blocks are loaded on demand."""
        # Initially, blocks should not be loaded
        self.assertFalse(self.lazy_document._blocks_loaded)
        
        # Accessing blocks should trigger loading
        blocks = self.lazy_document.blocks
        
        # Blocks should now be loaded
        self.assertTrue(self.lazy_document._blocks_loaded)
        self.assertEqual(len(blocks), len(self.test_blocks))
        self.mock_client.get_document_content.assert_called_once()
    
    def test_lazy_tree_building(self):
        """Test that tree is built on demand."""
        # Initially, tree should not be built
        self.assertFalse(self.lazy_document._tree_loaded)
        
        # Accessing tree-dependent operations should trigger tree building
        markdown = self.lazy_document.to_markdown()
        
        # Tree should now be built
        self.assertTrue(self.lazy_document._tree_loaded)
        self.assertIsNotNone(self.lazy_document.tree)
        self.mock_client.get_document_content.assert_called_once()
    
    def test_preview_methods(self):
        """Test preview methods trigger lazy loading."""
        # Preview methods should trigger block loading
        preview = self.lazy_document.preview_text(n_chars=200)
        
        # Blocks should now be loaded
        self.assertTrue(self.lazy_document._blocks_loaded)
        self.assertGreater(len(preview), 0)
        self.mock_client.get_document_content.assert_called_once()
    
    def test_direct_block_assignment(self):
        """Test that directly assigning blocks sets loaded flag."""
        new_blocks = [
            Block(id="new1", type="paragraph", content="New content")
        ]
        
        # Assign blocks directly
        self.lazy_document.blocks = new_blocks
        
        # Blocks should be marked as loaded, no client calls needed
        self.assertTrue(self.lazy_document._blocks_loaded)
        self.assertEqual(len(self.lazy_document.blocks), len(new_blocks))
        self.mock_client.get_document_content.assert_not_called()
    
    def test_client_error_handling(self):
        """Test handling of client errors during lazy loading."""
        # Set up client to raise an exception
        self.mock_client.get_document_content.side_effect = Exception("API error")
        
        # Accessing blocks should try to load, but handle the error
        blocks = self.lazy_document.blocks
        
        # Blocks should remain empty but loading was attempted
        self.assertEqual(len(blocks), 0)
        self.mock_client.get_document_content.assert_called_once()
    
    def test_no_client_provided(self):
        """Test behavior when no client is provided."""
        # Create a lazy document without a client
        no_client_doc = LazyDocument(
            id="doc_456",
            title="No Client Doc",
            created_time=datetime.now(),
            last_edited_time=datetime.now(),
            client=None
        )
        
        # Accessing blocks should not crash
        blocks = no_client_doc.blocks
        
        # Blocks should remain empty
        self.assertEqual(len(blocks), 0)


class TestLazyDocumentCollection(unittest.TestCase):
    """Test suite for LazyDocumentCollection class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock(spec=NotionClient)
        
        # Prepare some test data
        self.test_documents = [
            Document(
                id="doc_1",
                title="First Document",
                created_time=datetime.now(),
                last_edited_time=datetime.now()
            ),
            Document(
                id="doc_2",
                title="Second Document",
                created_time=datetime.now(),
                last_edited_time=datetime.now()
            ),
            Document(
                id="doc_3",
                title="Project Notes",
                created_time=datetime.now(),
                last_edited_time=datetime.now()
            )
        ]
        
        # Set up mock client to return the test documents
        self.mock_client.list_documents.return_value = self.test_documents
        
        # Mock get_document_content to return the document and empty blocks
        self.mock_client.get_document_content.return_value = (self.test_documents[0], [])
        
        # Create collection for testing
        self.collection = LazyDocumentCollection(
            client=self.mock_client,
            preload_metadata=True
        )
    
    def test_preload_metadata(self):
        """Test that metadata is preloaded."""
        # Collection should have all test documents
        self.assertEqual(len(self.collection.documents), len(self.test_documents))
        
        # Verify document IDs are in the collection
        for doc in self.test_documents:
            self.assertIn(doc.id, self.collection.documents)
        
        # Check that client was called to list documents
        self.mock_client.list_documents.assert_called_once()
        
        # Check that get_document_content was not called during preload
        self.mock_client.get_document_content.assert_not_called()
    
    def test_get_document(self):
        """Test getting a document by ID."""
        # Get a document that's already in the collection
        doc = self.collection.get_document("doc_1")
        
        # Document should be found and no content should be loaded
        self.assertIsNotNone(doc)
        self.assertEqual(doc.id, "doc_1")
        self.mock_client.get_document_content.assert_not_called()
        
        # Get a document that's not in the collection
        self.collection.documents = {}  # Clear the collection
        doc = self.collection.get_document("doc_1")
        
        # Document should be loaded from client
        self.assertIsNotNone(doc)
        self.assertEqual(doc.id, "doc_1")
        self.mock_client.get_document_content.assert_called_once()
    
    def test_search_documents_by_title(self):
        """Test searching documents by title."""
        # Search for a term that matches one document
        results = self.collection.search_documents("Project", search_titles=True)
        
        # Should find the document with "Project" in the title
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "doc_3")
        
        # No content should be loaded
        self.mock_client.get_document_content.assert_not_called()
    
    @patch('doctree_nlp.lazy_document.LazyDocument._load_blocks_if_needed')
    def test_search_documents_by_content(self, mock_load):
        """Test searching documents by content."""
        # Set up some content for testing
        for doc_id in self.collection.documents:
            self.collection.documents[doc_id].blocks = [
                Block(id=f"b_{doc_id}", type="paragraph", content=f"Content for {doc_id}")
            ]
            self.collection.documents[doc_id]._blocks_loaded = True
        
        # Search for content
        results = self.collection.search_documents(
            "Content for doc_2", 
            search_titles=False,
            search_content=True
        )
        
        # Should find the document with matching content
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "doc_2")
    
    def test_batch_preload(self):
        """Test batch preloading documents."""
        # Set up mocks for lazy documents
        for doc_id in self.collection.documents:
            self.collection.documents[doc_id]._load_blocks_if_needed = MagicMock()
        
        # Batch preload documents
        self.collection.batch_preload(["doc_1", "doc_3"])
        
        # Check that load was called for the correct documents
        self.collection.documents["doc_1"]._load_blocks_if_needed.assert_called_once()
        self.collection.documents["doc_3"]._load_blocks_if_needed.assert_called_once()
        self.collection.documents["doc_2"]._load_blocks_if_needed.assert_not_called()
    
    def test_clear_loaded_content(self):
        """Test clearing loaded content."""
        # Set up documents with some content
        for doc_id in self.collection.documents:
            doc = self.collection.documents[doc_id]
            # Add blocks directly
            doc.blocks = [Block(id=f"b_{doc_id}", type="paragraph", content="Some content")]
            
            # Use direct attribute setting to avoid validation issues
            object.__setattr__(doc, '_blocks_loaded', True)
            
            # Add a fake tree property 
            fake_tree = DocTree()
            object.__setattr__(doc, 'tree', fake_tree)
            object.__setattr__(doc, '_tree_loaded', True)
        
        # Clear loaded content but keep metadata
        self.collection.clear_loaded_content(keep_metadata=True)
        
        # Documents should still exist, but content should be cleared
        self.assertEqual(len(self.collection.documents), len(self.test_documents))
        for doc_id in self.collection.documents:
            doc = self.collection.documents[doc_id]
            self.assertEqual(len(doc.blocks), 0)
            self.assertFalse(doc._blocks_loaded)
            self.assertIsNone(doc.tree)
            self.assertFalse(doc._tree_loaded)
        
        # Set up again
        for doc_id in self.collection.documents:
            doc = self.collection.documents[doc_id]
            doc.blocks = [Block(id=f"b_{doc_id}", type="paragraph", content="Some content")]
            doc._blocks_loaded = True
        
        # Clear everything including metadata
        self.collection.clear_loaded_content(keep_metadata=False)
        
        # Collection should be empty
        self.assertEqual(len(self.collection.documents), 0)


class TestLazyDocumentFactory(unittest.TestCase):
    """Test suite for LazyDocument factory function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock(spec=NotionClient)
        
        # Prepare a test document
        self.test_document = Document(
            id="doc_123",
            title="Test Document",
            created_time=datetime.now(),
            last_edited_time=datetime.now()
        )
        
        # Set up mock client to return the test document
        self.mock_client._get_document_metadata.return_value = self.test_document
    
    def test_create_lazy_document(self):
        """Test creating a lazy document."""
        # Create a lazy document
        lazy_doc = create_lazy_document("doc_123", self.mock_client)
        
        # Check that the lazy document was created correctly
        self.assertIsNotNone(lazy_doc)
        self.assertEqual(lazy_doc.id, "doc_123")
        self.assertEqual(lazy_doc.title, "Test Document")
        self.assertFalse(lazy_doc._blocks_loaded)
        self.assertFalse(lazy_doc._tree_loaded)
        
        # Check that client methods were called
        self.mock_client._get_document_metadata.assert_called_once_with("doc_123")
    
    def test_create_lazy_document_not_found(self):
        """Test creating a lazy document when the document is not found."""
        # Set up mock client to return None
        self.mock_client._get_document_metadata.return_value = None
        
        # Try to create a lazy document
        lazy_doc = create_lazy_document("doc_not_found", self.mock_client)
        
        # Should return None
        self.assertIsNone(lazy_doc)
        self.mock_client._get_document_metadata.assert_called_once_with("doc_not_found")


if __name__ == '__main__':
    unittest.main()