from pydantic import BaseModel
from typing import Literal, Optional, Any

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

class ToolCall(BaseModel):
  function_name: str
  arguments: dict

class ToolResponse(BaseModel):
  name: str
  content: Any

class AiChatResponse(BaseModel):
  tool_selected: Optional[ToolCall] = None
  tool_finished: Optional[ToolResponse] = None
  content: Optional[str] = None

class Transcription(BaseModel):
  text: str

class TimeseriesReading(BaseModel):
  ts: str
  value: float
  timeseriesid: str

class PortfolioModel(BaseModel):
  name: str
  uri: str