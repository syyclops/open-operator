from typing import List
from abc import ABC, abstractmethod
from ..embeddings.embeddings import Embeddings
from openoperator.types import DocumentMetadataChunk 

class VectorStore(ABC):
  """
  A vector store is a database that stores text embeddings.
    
  Its responsibilities are:
  - Create text embeddings for documents and upload to the vector store
  - Search the vector store for similar documents
  """
  @abstractmethod
  def __init__(self, embeddings: Embeddings) -> None:
    pass
      
  def add_documents(self, documents: List[DocumentMetadataChunk]) -> None:
    """
    Creates text embeddings for a list of documents and uploads them to the vector store.
    """

  def delete_documents(self, filter: dict) -> None:
    """
    Deletes documents from the vector store.
    """
  
  def similarity_search(self, query: str, limit: int, filter: dict | None = None) -> list:
    """
    Search for similar documents in the vector store.
    """