from typing import List
from openoperator.domain.model.document import DocumentMetadataChunk
from abc import ABC, abstractmethod

class DocumentLoader(ABC):
  @abstractmethod 
  def load(self, file_content: bytes, file_path: str) -> List[DocumentMetadataChunk]:
    """
    Load a document from a file.
    """