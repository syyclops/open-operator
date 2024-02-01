from typing import List
from abc import ABC, abstractmethod
from ..embeddings.embeddings import Embeddings
from ..schema.document import Document

class VectorStore(ABC):
    """
    This class is focused on managing the vector store for the assistant.
    Its responsibilities are:
    - Create text embeddings for documents and upload to the vector store
    - Search the vector store for similar documents
    """
    @abstractmethod
    def __init__(self, embeddings: Embeddings) -> None:
        pass
        
    def add_documents(self, documents: List[Document]) -> None:
        """
        Creates text embeddings for a list of documents and uploads them to the vector store.
        """
        pass
    
    def similarity_search(self, query: str, limit: int, filter: dict | None = None) -> list:
        """
        Search for similar documents in the vector store.
        """
        pass
        
