from pydantic import BaseModel
from typing import Literal

class DocumentQuery(BaseModel):
    query: str
    limit: int = 15
    file_url: str = None

class Document:
    def __init__(self, text: str, metadata):
        self.text = text
        self.metadata = metadata

class Message(BaseModel):
    content: str
    role: Literal['user', 'assistant']