import os
from openai import OpenAI
from openai.types import Embedding
from .embeddings import Embeddings

class OpenAIEmbeddings(Embeddings):
    def __init__(self, openai_api_key: str | None = None) -> None:
        # Create openai client
        if openai_api_key is None:
            openai_api_key = os.environ['OPENAI_API_KEY']
        openai = OpenAI(api_key=openai_api_key)
        self.embeddings = openai.embeddings
        self.model = "text-embedding-3-small" 
    
    def create_embeddings(self, texts: list[str]) -> list[Embedding]:
        """
        Convert a list of strings into embeddings.
        """
        embeddings = self.embeddings.create(
                        model=self.model,
                        input=texts,
                        encoding_format="float"
                    )
        
        return embeddings.data