import psycopg
from pgvector.psycopg import register_vector
import json
import numpy as np
import os
from .embeddings import Embeddings
from .document_loader import Document

class VectorStore():
    """
    This class is focused on managing the vector store for the assistant.
    Its responsibilities are:
    - Create text embeddings for documents and upload to the vector store
    - Search the vector store for similar documents
    """
    def __init__(self, embeddings: Embeddings, collection_name: str, connection_string: str) -> None:
        if connection_string is None:
            connection_string = os.environ['POSTGRES_CONNECTION_STRING']
        if collection_name is None:
            collection_name = os.environ['POSTGRES_EMBEDDINGS_TABLE']

        self.embeddings = embeddings

        # Connect to postgres
        self.conn = psycopg.connect(connection_string)
        self.collection_name = collection_name

        # Make sure pgvector is installed and table is created
        self.conn.autocommit = True
        with self.conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
            register_vector(self.conn)

            # Check if table exists
            cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{collection_name}\')')
            exists = cur.fetchone()[0]

            # Create table if it doesn't exist
            if not exists:
                cur.execute(f'CREATE TABLE {collection_name} (id bigserial PRIMARY KEY, content text, metadata jsonb, embedding vector(1536));')

    def add_documents(self, documents: list[Document]) -> None:
        """
        Creates text embeddings for a list of documents and uploads them to the vector store.
        """
        with self.conn.cursor() as cur:
            # Create the embeddings
            docs = [doc.text for doc in documents]
            embeddings = self.embeddings.create_embeddings(texts=docs)
            
            # Insert into postgres
            for i, doc in enumerate(documents):
                text = doc.text
                metadata = json.dumps(doc.metadata)
                embedding = np.array(embeddings[i].embedding)

                cur.execute(f'INSERT INTO {self.collection_name} (content, metadata, embedding) VALUES (%s, %s, %s)', (text, metadata, embedding))
    
    def similarity_search(self, query: str, limit: int, filter: dict | None = None) -> list:
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

        query += f" ORDER BY embedding <-> %s LIMIT %s"
        params.append(embedding)
        params.append(limit)
        
        # Query postgres
        with self.conn.cursor() as cur:
            register_vector(self.conn)
            records = cur.execute(query, params).fetchall()
            
            # Convert the list of tuples to a list of dicts
            data = [{"content": record[0], "metadata": record[1]} for record in records]

            return data
