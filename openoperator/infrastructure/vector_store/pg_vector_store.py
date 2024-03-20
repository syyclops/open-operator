from pgvector.psycopg import register_vector
import json
import numpy as np
import os
from typing import List
from ..postgres import Postgres
from .vector_store import VectorStore
from ..embeddings.embeddings import Embeddings
from openoperator.domain.model.document import DocumentMetadataChunk, DocumentMetadata

class PGVectorStore(VectorStore):
  """
  PG Vector Store is a vector store that uses Postgres to store text embeddings.
    
  Its responsibilities are:
  - Create text embeddings for documents and upload to the vector store
  - Search the vector store for similar documents
  """
  def __init__(self, postgres: Postgres, embeddings: Embeddings, collection_name: str | None = None) -> None:
    if collection_name is None:
      collection_name = os.environ['POSTGRES_EMBEDDINGS_TABLE']
    self.postgres = postgres
    self.embeddings = embeddings

    try:
      # Connect to postgres
      self.collection_name = collection_name

      # Make sure pgvector is installed and table is created
      self.postgres.conn.autocommit = True
      with self.postgres.cursor() as cur:
        cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
        register_vector(self.postgres.conn)

        # Check if table exists
        cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{collection_name}\')')
        exists = cur.fetchone()[0]

        # Create table if it doesn't exist
        if not exists:
          cur.execute(f'CREATE TABLE {collection_name} (id bigserial PRIMARY KEY, content text, metadata jsonb, embedding vector(1536));')
    except Exception as e:
      raise e

  def add_documents(self, documents: List[DocumentMetadataChunk]) -> None:
    """
    Creates text embeddings for a list of documents and uploads them to the vector store.
    """
    with self.postgres.cursor() as cur:
      # Create the embeddings
      docs = [doc.content for doc in documents]
      embeddings = self.embeddings.create_embeddings(docs)
      
      # Insert into postgrs
      for i, doc in enumerate(documents):
        text = doc.content
        metadata = json.dumps(doc.metadata)
        embedding = np.array(embeddings[i].embedding)

        cur.execute(f'INSERT INTO {self.collection_name} (content, metadata, embedding) VALUES (%s, %s, %s)', (text, metadata, embedding))
    
  def similarity_search(self, query: str, limit: int, filter: dict | None = None) -> list[DocumentMetadataChunk]:
    """
    Search for similar documents in the vector store.
    """
    # Get embedding from OpenAI
    embeddings = self.embeddings.create_embeddings(texts=[query])
    embedding = np.array(embeddings[0].embedding)

    # Prepare base SQL query
    query  = f"SELECT content, metadata FROM {self.collection_name} "
    params = []

    # Add filter to query
    if filter is not None:
      query += " WHERE "
      for i, (key, value) in enumerate(filter.items()):
        # Ensure the value is a string
        value_str = str(value)
        query += f"metadata->>'{key}' = %s"
        params.append(value_str)
        if i != len(filter) - 1:
          query += " AND "

    query += " ORDER BY embedding <=> %s LIMIT %s"
    params.append(embedding)
    params.append(limit)

    # Query postgres
    with self.postgres.cursor() as cur:
      register_vector(self.postgres.conn)
      records = cur.execute(query, params).fetchall()
      
      # Convert the list of tuples to a list of dicts
      data = [DocumentMetadataChunk(content=record[0], metadata=DocumentMetadata(
        filename=record[1]['filename'],
        portfolio_uri=record[1]['portfolio_uri'],
        facility_uri=record[1]['facility_uri'],
        document_uri=record[1]['document_uri'] if 'document_uri' in record[1] else None,
        document_url=record[1]['document_url'] if 'document_url' in record[1] else None,
        filetype=record[1]['filetype'] if 'filetype' in record[1] else None,
        page_number=record[1]['page_number']  if 'page_number' in record[1] else None 
      )) for record in records]

      return data
    
  def list_documents(self, filter: dict | None = None) -> list[DocumentMetadataChunk]:
    """
    List all documents in the vector store.
    """
    # Prepare base SQL query
    query  = f"SELECT content, metadata FROM {self.collection_name} "
    params = []

    # Add filter to query
    if filter is not None:
      query += " WHERE "
      for i, (key, value) in enumerate(filter.items()):
        # Ensure the value is a string
        value_str = str(value)
        query += f"metadata->>'{key}' = %s"
        params.append(value_str)
        if i != len(filter) - 1:
          query += " AND "

    # Query postgres
    with self.postgres.cursor() as cur:
      records = cur.execute(query, params).fetchall()
      
      # Convert the list of tuples to a list of dicts
      data = [DocumentMetadataChunk(content=record[0], metadata=DocumentMetadata(
        filename=record[1]['filename'],
        portfolio_uri=record[1]['portfolio_uri'],
        facility_uri=record[1]['facility_uri'],
        document_uri=record[1]['document_uri'] ,
        document_url=record[1]['document_url'],
        filetype=record[1]['filetype'],
        page_number=record[1]['page_number'] if 'page_number' in record[1] else None 
      )) for record in records]

      return data

  def delete_documents(self, filter: dict) -> None:
    """
    Deletes documents from the vector store.
    """
    with self.postgres.cursor() as cur:
      query = f"DELETE FROM {self.collection_name} WHERE "
      params = []
      for i, (key, value) in enumerate(filter.items()):
        query += f"metadata->>'{key}' = %s"
        params.append(str(value))
        if i != len(filter) - 1:
          query += " AND "
      
      cur.execute(query, params)