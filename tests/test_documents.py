from openoperator.core import Documents
import unittest
from unittest.mock import Mock, patch

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


if __name__ == '__main__':
    unittest.main()
