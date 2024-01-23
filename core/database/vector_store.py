from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings

class VectorStore():
    def __init__(self, collection_name: str, connection_string: str) -> None:
        embeddings = OpenAIEmbeddings()
        self.vector_store = PGVector(collection_name=collection_name, connection_string=connection_string, embedding_function=embeddings)

    def add_documents(self, documents: list) -> None:
        self.vector_store.add_documents(documents)

    def similarity_search(self, query: str, k: int) -> list:
        return self.vector_store.similarity_search(query, k)
