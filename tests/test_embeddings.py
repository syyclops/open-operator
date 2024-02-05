import unittest
from unittest.mock import patch, MagicMock
from openoperator.embeddings import OpenAIEmbeddings  # Adjust the import based on your project structure

class TestOpenAIEmbeddings(unittest.TestCase):
    @patch('openoperator.embeddings.openai_embeddings.os.environ')
    @patch('openoperator.embeddings.openai_embeddings.OpenAI')
    def test_create_embeddings_single_chunk(self, mock_OpenAI, mock_environ):
        # Setup mock for API key environment variable
        mock_environ.get.return_value = 'test_api_key'
    
        # Setup mock for OpenAI embeddings create method
        mock_client = MagicMock()
        mock_OpenAI.return_value = mock_client
        mock_client.embeddings.create.return_value = MagicMock(data=[{"embedding": [0.1, 0.2, 0.3]}])
        
        # Initialize OpenAIEmbeddings instance
        embeddings_instance = OpenAIEmbeddings()
        
        # Call create_embeddings with test data
        texts = ["This is a test sentence."]
        embeddings = embeddings_instance.create_embeddings(texts)
        
        # Assertions to verify behavior
        self.assertEqual(len(embeddings), 1)
        self.assertEqual(embeddings[0]["embedding"], [0.1, 0.2, 0.3])
        mock_client.embeddings.create.assert_called_once_with(model="text-embedding-3-small", input=texts, encoding_format="float")



if __name__ == '__main__':
    unittest.main()
