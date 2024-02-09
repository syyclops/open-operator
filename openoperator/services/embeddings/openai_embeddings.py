import os
from openai import OpenAI
from .embeddings import Embeddings
import tiktoken

class OpenAIEmbeddings(Embeddings):
    def __init__(self, openai_api_key: str | None = None) -> None:
        if openai_api_key is None:
            openai_api_key = os.environ['OPENAI_API_KEY']
        openai = OpenAI(api_key=openai_api_key)
        self.embeddings = openai.embeddings
        self.model = "text-embedding-3-small"

    def chunk_text(self, texts: list[str], max_tokens: int) -> list:
        """
        Split a list of texts into chunks that do not exceed the max tokens.
        """
        encoding = tiktoken.get_encoding('cl100k_base')
        chunks = []
        current_chunk = []
        current_chunk_text = ""

        for text in texts:
            # Simulate adding this text to the current chunk
            test_chunk_text = ' '.join([current_chunk_text, text]).strip()
            test_chunk_token_count = len(encoding.encode(test_chunk_text))

            if test_chunk_token_count <= max_tokens:
                # If the test chunk does not exceed the max tokens, update the current chunk and text
                current_chunk.append(text)
                current_chunk_text = test_chunk_text
            else:
                # If the test chunk exceeds the max tokens, finalize the current chunk and start a new one
                chunks.append(current_chunk)
                current_chunk = [text]
                current_chunk_text = text

        # Don't forget to add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)

        return chunks
     
    def create_embeddings(self, texts: list[str]) -> list:
        """
        Convert a list of strings into embeddings, ensuring each chunk does not exceed the token limit.
        """
        max_tokens = 8191  # Max tokens allowed
        chunks = self.chunk_text(texts, max_tokens)
        embeddings = []
        for chunk in chunks:
            try:
                # Assuming self.embeddings.create correctly handles a list of strings as input
                chunk_embeddings = self.embeddings.create(
                    model=self.model,
                    input=chunk,  # This should be correctly formatted per the API's expectations
                    encoding_format="float"
                )
                embeddings.extend(chunk_embeddings.data)
            except Exception as e:
                print(f"Error processing chunk: {e}")

        return embeddings
