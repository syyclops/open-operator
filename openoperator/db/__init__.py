from .vector_store import VectorStore
import os

vector_store = VectorStore(
    collection_name=os.environ.get("POSTGRES_EMBEDDINGS_TABLE"),
    connection_string=os.environ.get("POSTGRES_CONN"),
)