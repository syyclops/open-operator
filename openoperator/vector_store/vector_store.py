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
                cur.execute(f'CREATE TABLE {collection_name} (id bigserial PRIMARY KEY, file_url text, portfolio_id text, building_id text, content text, metadata jsonb, embedding vector(1536));')

    def add_documents(self, documents: list, portfolio_id: str, building_id: str, file_url: str) -> None:
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

                cur.execute(f'INSERT INTO {self.collection_name} (content, metadata, embedding, portfolio_id, building_id, file_url) VALUES (%s, %s, %s, %s, %s, %s)', (text, metadata, embedding, portfolio_id, building_id, file_url))
        
        
    def similarity_search(self, query: str, limit: int, portfolio_id: str, building_id: str = None) -> list:
        # Get embedding from OpenAI
        embeddings = self.openai.embeddings.create(
                        model="text-embedding-3-small",
                        input=query,
                        encoding_format="float"
                    )
        embedding = np.array(embeddings.data[0].embedding)

        # Prepare base SQL query
        query  = f"SELECT content, metadata FROM {self.collection_name} WHERE portfolio_id = %s"
        params = [portfolio_id]

        # Add building_id condition if provided
        if building_id:
            query += " AND building_id = %s"
            params.append(building_id)

        # Add order by and limit clause
        query += " ORDER BY embedding <-> %s LIMIT %s"
        params.extend([embedding, limit])

        # Query postgres
        with self.conn as cur:
            register_vector(self.conn)
            records = cur.execute(query, params).fetchall()
            
            # Convert the list of tuples to a list of dicts
            data = [{"content": record[0], "metadata": record[1]} for record in records]

            return data
