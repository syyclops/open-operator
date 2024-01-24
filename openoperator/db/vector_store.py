from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
import psycopg
from pgvector.psycopg import register_vector


class VectorStore():
    def __init__(self, collection_name: str, connection_string: str) -> None:
        self.conn = psycopg.connect(connection_string)

        self.conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        register_vector(self.conn)

        self.conn.execute('CREATE TABLE items (id bigserial PRIMARY KEY, embedding vector(3))')

        embeddings = OpenAIEmbeddings()
        self.vector_store = PGVector(collection_name=collection_name, connection_string=connection_string, embedding_function=embeddings)

    def add_documents(self, documents: list) -> None:
        self.vector_store.add_documents(documents)

    def similarity_search(self, query: str, k: int) -> list:
        return self.vector_store.similarity_search(query, k)
