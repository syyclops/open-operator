from unittest.mock import Mock, patch
from openoperator.services.document_loader import UnstructuredDocumentLoader
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
        {"text": "This is a test", "metadata": {"title": "Test Document"}},
        {"text": "Another test", "metadata": {"title": "Another Test Document"}},
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
    assert documents[0].text == "This is a test"
    assert documents[0].metadata == {"title": "Test Document"}

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