import psycopg
from pgvector.psycopg import register_vector
from openai import OpenAI
import json
import numpy as np

class VectorStore():
    def __init__(self, openai: OpenAI, collection_name: str, connection_string: str) -> None:
        self.openai = openai

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

    def add_documents(self, documents: list) -> None:
        with self.conn as cur:
            # Create the embeddings
            docs = [doc['text'] for doc in documents]
            embeddings = self.openai.embeddings.create(
                            model="text-embedding-3-small",
                            input=docs,
                            encoding_format="float"
                        )
            
            # Insert into postgres
            for i, doc in enumerate(documents):
                text = doc['text']
                metadata = json.dumps(doc['metadata'])
                embedding = np.array(embeddings.data[i].embedding)

                cur.execute(f'INSERT INTO {self.collection_name} (content, metadata, embedding) VALUES (%s, %s, %s)', (text, metadata, embedding))
        
        
    def similarity_search(self, query: str, limit: int) -> list:
        # Get embedding from OpenAI
        embeddings = self.openai.embeddings.create(
                        model="text-embedding-3-small",
                        input=query,
                        encoding_format="float"
                    )
        embedding = np.array(embeddings.data[0].embedding)
        
        # Query postgres
        with self.conn as cur:
            register_vector(self.conn)
            records = cur.execute(f'SELECT content, metadata FROM {self.collection_name} ORDER BY embedding <-> %s LIMIT {limit}', (embedding,)).fetchall()
            
            # Convert the list of tuples to a list of dicts
            data = [{"content": record[0], "metadata": record[1]} for record in records]

            return data
