from unittest.mock import Mock, patch
from openoperator.services.document_loader import UnstructuredDocumentLoader
from openoperator.types import DocumentMetadata
import os
import unittest

class TestUnstructuredDocumentLoader(unittest.TestCase):
  @patch('openoperator.services.document_loader.unstructured_document_loader.UnstructuredClient')
  def test_load(self, mock_UnstructuredClient):
    # Setup mock for API key environment variable
    os.environ['UNSTRUCTURED_API_KEY'] = 'test_api_key'
    os.environ['UNSTRUCTURED_URL'] = 'test_url'

    # Setup mock for UnstructuredClient
    mock_client = Mock()
    mock_UnstructuredClient.return_value = mock_client
    mock_client.general.partition.return_value = Mock(
      elements=[
        {"text": "This is a test", "metadata": {"filename": "Test Document", "portfolio_uri": "test_portfolio_uri", "facility_uri": "test_facility_uri", "document_uri": "test_document_uri", "document_url": "test_document_url", "filetype": "test_filetype", "page_number": 1}},
        {"text": "Another test", "metadata": {"filename": "Another Test Document", "portfolio_uri": "test_portfolio_uri", "facility_uri": "test_facility_uri", "document_uri": "test_document_uri", "document_url": "test_document_url", "filetype": "test_filetype", "page_number": 2}}
      ]
    )

    # Initialize UnstructuredDocumentLoader instance
    document_loader = UnstructuredDocumentLoader()

    # Call load with test data
    file_content = b"test content"
    file_path = "test_path"
    documents = document_loader.load(file_content, file_path)

    # Assertions to verify behavior
    assert len(documents) == 2
    assert documents[0].content == "This is a test"
    assert documents[0].metadata == DocumentMetadata(filename="Test Document", portfolio_uri="test_portfolio_uri", facility_uri="test_facility_uri", document_uri="test_document_uri", document_url="test_document_url", filetype="test_filetype", page_number=1)

  @patch('openoperator.services.document_loader.unstructured_document_loader.UnstructuredClient')
  def test_invalid_credentials(self, mock_UnstructuredClient):
    # Setup mock for API key and URL environment variables
    os.environ['UNSTRUCTURED_API_KEY'] = 'invalid_api_key'
    os.environ['UNSTRUCTURED_URL'] = 'invalid_url'

    # Setup the mock to raise an Exception for invalid credentials
    mock_client = Mock()
    mock_UnstructuredClient.return_value = mock_client
    mock_client.general.partition.side_effect = Exception("Invalid API Key")    

    # Initialize UnstructuredDocumentLoader instance
    document_loader = UnstructuredDocumentLoader()

    # Define the file content and path to simulate the call
    file_content = b"test content"
    file_path = "test_path"

    # Execute the load function and assert it raises an SDKError
    with self.assertRaises(Exception) as context:
      _ = document_loader.load(file_content, file_path)

    # You can also check the message of the exception if necessary
    self.assertTrue("Invalid API Key" in str(context.exception))