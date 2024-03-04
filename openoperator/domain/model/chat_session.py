from pydantic import BaseModel
from typing import List, Optional, Literal

class Message(BaseModel): 
  content: str
  role: Literal['user', 'assistant']

class LLMChatResponse(BaseModel):
  type: Literal['tool_selected', 'tool_finished', 'content']
  tool_id: Optional[str] = None
  tool_name: Optional[str] = None
  tool_response: Optional[List] = None
  tool_args: Optional[dict] = None
  content: Optional[str] = None

# New Domain Entity
class ChatSession:
  def __init__(self, session_id: str):
    self.session_id = session_id
    self.messages: List[Message] = []

  def add_message(self, message: Message):
    self.messages.append(message)