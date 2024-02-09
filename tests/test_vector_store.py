from unittest.mock import MagicMock, patch
from openoperator.services.vector_store.pg_vector_store import PGVectorStore
import os
from openoperator.types import Document
from openoperator.services.embeddings import Embeddings
from openai.types import Embedding

@patch('openoperator.services.vector_store.pg_vector_store.psycopg')
@patch('openoperator.services.vector_store.pg_vector_store.register_vector')
def test_add_documents(mock_register_vector, mock_psycopg):
    # Setup environment variables
    os.environ['POSTGRES_CONNECTION_STRING'] = 'connection_string'
    os.environ['POSTGRES_EMBEDDINGS_TABLE'] = 'table_name'

    # Create a mock psycopg instance
    mock_conn = MagicMock()
    mock_psycopg.connect.return_value = mock_conn

    # Create a mock cursor instance
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock the embeddings
    mock_embeddings = MagicMock(spec=Embeddings)

    # Initialize PGVectorStore, this should use the mocked psycopg
    store = PGVectorStore(mock_embeddings)

    mock_register_vector.assert_called_once_with(mock_conn)

    # Verify psycopg.connect was called correctly
    mock_psycopg.connect.assert_called_once_with('connection_string')

    # Verify cursor was called correctly
    mock_conn.cursor.assert_called_once()

    # Perform the add_documents
    documents = [
        Document(text='doc1', metadata={'key': 'value'}),
        Document(text='doc2', metadata={'key': 'value'})
    ]
    mock_embeddings.create_embeddings.return_value = [
        Embedding(embedding=[1, 2, 3], index=0, object='embedding'),
        Embedding(embedding=[4, 5, 6], index=1, object='embedding')
    ]
    store.add_documents(documents)

    assert mock_conn.cursor.call_count == 2