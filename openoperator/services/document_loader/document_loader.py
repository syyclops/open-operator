from typing import List
from openoperator.types import Document
from abc import ABC, abstractmethod

class DocumentLoader(ABC):
    @abstractmethod 
    def load(self, file_content: bytes, file_path: str) -> List[Document]:
        pass
     