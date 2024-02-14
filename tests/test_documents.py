from openoperator.core import Documents
import unittest
from unittest.mock import Mock, patch, MagicMock

class TestDocuments(unittest.TestCase):
  def setUp(self) -> None:
    self.blob_store = Mock()
    self.document_loader = Mock()
    self.vector_store = Mock()
    self.knowledge_graph = Mock()
    self.facility = Mock()
    self.documents = Documents(self.facility, self.knowledge_graph, self.blob_store, self.document_loader, self.vector_store)

  def setup_session_mock(self):
    # Create the session mock
    session_mock = Mock()
    # Simulate entering the context
    session_mock.__enter__ = Mock(return_value=session_mock)
    # Simulate exiting the context
    session_mock.__exit__ = Mock(return_value=None)
    # Configure the knowledge_graph to return this session mock
    self.knowledge_graph.create_session.return_value = session_mock
    return session_mock

  def test_list(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        "d": {
          "url": "test_url",
          "name": "test_name",
          "extractionStatus": "success"
        }
      }
    ]
    session_mock.run.return_value = mock_query_result

    documents = self.documents.list()

    assert len(documents) == 1
    assert documents[0]['url'] == "test_url"
    assert documents[0]['name'] == "test_name"
    assert documents[0]['extractionStatus'] == "success"
    
  def test_list_no_results(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.data.return_value = []
    session_mock.run.return_value = mock_query_result

    documents = self.documents.list()

    assert len(documents) == 0

  def test_upload(self):
    file_content = b'file_content'
    file_name = 'file_name.docx'
    file_type = 'test_type'
    file_url = 'http://example.com/file.docx'

    # Mock the blob_store.upload_file method to return a file_url or a thumbnail_url
    self.blob_store.upload_file.side_effect = [file_url]

    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution for creating a document
    mock_query_result = Mock()
    document_node = {"name": file_name, "url": file_url, "extractionStatus": "pending"}
    mock_query_result.data.return_value = [ {"d": document_node} ]
    session_mock.run.return_value = mock_query_result

    # Execute the upload method
    result_document = self.documents.upload(file_content, file_name, file_type)

    # Verify the result
    self.assertEqual(result_document, document_node)
    self.assertEqual(self.blob_store.upload_file.call_count, 1)
    self.blob_store.upload_file.assert_called_with(file_content=file_content, file_name=file_name, file_type=file_type)
    session_mock.run.assert_called_once()
    
  def test_upload_pdf(self):
    file_content = b'file_content'
    file_name = 'file_name.pdf'
    file_type = 'application/pdf'
    file_url = 'http://example.com/file.pdf'
    thumbnail_url = 'http://example.com/file_thumbnail.png'

    # Mock fitz.open to return a mock document
    fitz_mock = Mock()
    fitz_mock.load_page.return_value = fitz_mock
    fitz_mock.get_pixmap.return_value = fitz_mock
    fitz_mock.tobytes.return_value = b'thumbnail_content'

    # Mock the blob_store.upload_file method to return a file_url or a thumbnail_url
    self.blob_store.upload_file.side_effect = [thumbnail_url, file_url]

    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution for creating a document
    mock_query_result = Mock()
    document_node = {"name": file_name, "url": file_url, "extractionStatus": "pending", "thumbnailUrl": thumbnail_url}  
    mock_query_result.data.return_value = [ {"d": document_node} ]
    session_mock.run.return_value = mock_query_result

    # Mock fitz.open and execute the upload method
    with patch('openoperator.core.documents.fitz.open', return_value=fitz_mock):
      result_document = self.documents.upload(file_content, file_name, file_type)

    # Verify the result
    self.assertEqual(result_document, document_node)
    self.assertEqual(self.blob_store.upload_file.call_count, 2)
    self.blob_store.upload_file.assert_any_call(file_content=b'thumbnail_content', file_name=f"{file_name}_thumbnail.png", file_type='image/png')
    self.blob_store.upload_file.assert_any_call(file_content=file_content, file_name=file_name, file_type=file_type)

  def test_update_extraction_status(self):
    url = "http://example.com/file.docx"
    status = "success"

    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution for updating a document
    mock_query_result = Mock()
    document_node = {"name": "test_name", "url": url, "extractionStatus": status}
    mock_query_result.data.return_value = [ {"d": document_node} ]
    session_mock.run.return_value = mock_query_result

    # Execute the update_extraction_status method
    result_document = self.documents.update_extraction_status(url, status)

    # Verify the result
    self.assertEqual(result_document, document_node)
    session_mock.run.assert_called_once()
    assert "MATCH (d:Document {url: $url})" in session_mock.run.call_args[0][0]
    assert "SET d.extractionStatus = $status" in session_mock.run.call_args[0][0]
    assert "RETURN d" in session_mock.run.call_args[0][0]

  def test_run_extraction_process(self):
    file_content = b'file_content'
    file_name = 'file_name.pdf'
    file_url = 'http://example.com/file.pdf'

    # Mock the document_loader.load method
    mock_document = MagicMock()
    mock_document.metadata = {}  # Add this line
    self.document_loader.load.return_value = [mock_document]

    # Mock the vector_store.add_documents method
    self.vector_store.add_documents = Mock()

    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution for updating a document
    mock_query_result = Mock()
    document_node = {"name": file_name, "url": file_url, "extractionStatus": "success"}
    mock_query_result.data.return_value = [ {"d": document_node} ]
    session_mock.run.return_value = mock_query_result

    # Execute the run_extraction_process method
    result_document = self.documents.run_extraction_process(file_content, file_name, file_url)

    # Verify the result
    self.assertEqual(result_document, document_node)
    self.document_loader.load.assert_called_once_with(file_content=file_content, file_path=file_name)
    self.vector_store.add_documents.assert_called_once_with([mock_document])
    session_mock.run.assert_called_once()
    assert "MATCH (d:Document {url: $url})" in session_mock.run.call_args[0][0]
    assert "SET d.extractionStatus = $status" in session_mock.run.call_args[0][0]
    assert "RETURN d" in session_mock.run.call_args[0][0]

  def test_delete(self):
    url = "http://example.com/file.docx"

    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution for deleting a document
    mock_query_result = Mock()
    document_node = {"name": "test_name", "url": url, "extractionStatus": "success"}
    mock_query_result.data.return_value = [ {"d": document_node} ]
    session_mock.run.return_value = mock_query_result

    # Execute the delete method
    self.documents.delete(url)

    # Verify the result
    session_mock.run.assert_called_once()
    self.blob_store.delete_file.assert_called_once_with(url)
    self.vector_store.delete_documents.assert_called_once_with(filter={"file_url": url})
    assert "MATCH (d:Document {url: $url})" in session_mock.run.call_args[0][0]
    assert "DETACH DELETE d" in session_mock.run.call_args[0][0]

  def test_search(self):
    params = {"query": "test_query"}

    # Mock the vector_store.search method
    self.vector_store.similarity_search.return_value = []

    # Execute the search method
    documents = self.documents.search(params)

    # Verify the result
    self.vector_store.similarity_search.assert_called_once_with(query=params["query"], limit=15, filter={"facility_uri": self.facility.uri})
    assert documents == []
        

if __name__ == '__main__':
  unittest.main()
