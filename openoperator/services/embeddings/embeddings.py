from abc import ABC, abstractmethod
from openai.types import Embedding

class Embeddings(ABC):
    @abstractmethod    
    def create_embeddings(self, texts: list[str]) -> list[Embedding]:
        """
        Convert a list of strings into embeddings.
        """
        pass