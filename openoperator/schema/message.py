from pydantic import BaseModel
from typing import Literal


class Message(BaseModel):
    content: str
    role: Literal['user', 'assistant']