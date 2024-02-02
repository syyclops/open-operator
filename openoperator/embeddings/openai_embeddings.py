import os
from openai import OpenAI
from openai.types import Embedding
from .embeddings import Embeddings
import tiktoken

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
        # Check token count
        encoding = tiktoken.get_encoding('cl100k_base')
        token_count = 0
        for text in texts:
            token_count += len(encoding.encode(text))

        max_tokens = 8000
        chunks = []

        if token_count > max_tokens:
            # Token count is greater than 8000, splitting the texts into chunks
            chunk = []
            chunk_token_count = 0
            for text in texts:
                text_tokens = len(encoding.encode(text))
                if chunk_token_count + text_tokens <= max_tokens:
                    chunk.append(text)
                    chunk_token_count += text_tokens
                else:
                    chunks.append(chunk)
                    chunk = [text]
                    chunk_token_count = text_tokens 
            chunks.append(chunk)
        else:
            chunks.append(texts)
        
        embeddings = []
        for chunk in chunks:
            chunk_embeddings = self.embeddings.create(
                model=self.model,
                input=chunk,
                encoding_format="float"
            )
            embeddings.extend(chunk_embeddings.data)

        return embeddings