from unittest.mock import MagicMock, patch
from openoperator.infrastructure.vector_store.pg_vector_store import PGVectorStore
from openoperator.infrastructure.postgres import Postgres
import os
from openoperator.types import DocumentMetadataChunk, DocumentMetadata
from openoperator.infrastructure.embeddings import Embeddings
from openai.types import Embedding

@patch('openoperator.services.vector_store.pg_vector_store.register_vector')
@patch('openoperator.services.postgres.Postgres')
def test_add_documents(mock_postgres, mock_register_vector):
  # Setup environment variables
  os.environ['POSTGRES_EMBEDDINGS_TABLE'] = 'table_name'

  # Create a mock Postgres instance
  mock_postgres_instance = MagicMock(spec=Postgres)
  mock_postgres.return_value = mock_postgres_instance

  # Mock the conn attribute
  mock_conn = MagicMock()
  mock_postgres_instance.conn = mock_conn

  # Create a mock cursor instance
  mock_cursor = MagicMock()
  mock_postgres_instance.cursor.return_value.__enter__.return_value = mock_cursor

  # Mock the embeddings
  mock_embeddings = MagicMock(spec=Embeddings)

  # Initialize PGVectorStore, this should use the mocked Postgres
  store = PGVectorStore(mock_postgres_instance, mock_embeddings)

  mock_register_vector.assert_called_once_with(mock_postgres_instance.conn)

  # Perform the add_documents
  documents = [
    DocumentMetadataChunk(content='doc1', metadata=DocumentMetadata(filename='test', portfolio_uri='test', facility_uri='test', document_uri='test', document_url='test', filetype='test', page_number=1)),
    DocumentMetadataChunk(content='doc2', metadata=DocumentMetadata(filename='test', portfolio_uri='test', facility_uri='test', document_uri='test', document_url='test', filetype='test', page_number=2))
  ]
  mock_embeddings.create_embeddings.return_value = [
    Embedding(embedding=[1, 2, 3], index=0, object='embedding'),
    Embedding(embedding=[4, 5, 6], index=1, object='embedding')
  ]
  store.add_documents(documents)

  # Verify cursor was called correctly
  assert mock_postgres_instance.cursor.call_count == 2

  # Verify execute was called correctly
  mock_cursor.execute.assert_called()