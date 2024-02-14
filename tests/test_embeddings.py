import unittest
from unittest.mock import patch, MagicMock
from openoperator.services.embeddings import OpenAIEmbeddings 

class TestOpenAIEmbeddings(unittest.TestCase):
  @patch('openoperator.services.embeddings.openai_embeddings.os.environ')
  @patch('openoperator.services.embeddings.openai_embeddings.OpenAI')
  def test_create_embeddings_single_chunk(self, mock_OpenAI, mock_environ):
    # Setup mock for API key environment variable
    mock_environ.get.side_effect = lambda k, d=None: 'test_api_key' if k == 'OPENAI_API_KEY' else d

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


  @patch('openoperator.services.embeddings.openai_embeddings.os.environ')
  @patch('openoperator.services.embeddings.openai_embeddings.OpenAI')
  def test_chunk_text(self, mock_OpenAI, mock_environ):
    mock_environ.get.side_effect = lambda k, d=None: 'test_api_key' if k == 'OPENAI_API_KEY' else d

    # Initialize OpenAIEmbeddings instance
    embeddings_instance = OpenAIEmbeddings()
    
    texts = ["Hello world", "This is a test", "Another test", "Yet another test"]
    max_tokens = 5 
    expected_chunks = [
      ['Hello world'], 
      ['This is a test'], 
      ['Another test', 'Yet another test']
    ]

    chunks = embeddings_instance.chunk_text(texts, max_tokens)

    # Assertions to verify behavior
    self.assertEqual(chunks, expected_chunks)


if __name__ == '__main__':
  unittest.main()