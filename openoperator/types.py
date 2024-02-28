from pydantic import BaseModel
from typing import Literal, Optional, List

## Document Loader
class DocumentQuery(BaseModel):
  query: str
  limit: int = 15
  doc_uri: str = None

class DocumentMetadataChunk(BaseModel):
  text: str
  metadata: dict

# Documents
class DocumentModel(BaseModel):
  extractionStatus: Literal['pending', 'success', 'failed']
  name: str
  uri: str
  url: str
  thumbnailUrl: str | None

## AI Chat
class Message(BaseModel): 
  content: str
  role: Literal['user', 'assistant']

class LLMChatResponse(BaseModel):
  type: Literal['tool_selected', 'tool_finished', 'content']
  tool_id: Optional[str] = None
  tool_name: Optional[str] = None
  tool_response: Optional[List] = None
  content: Optional[str] = None

class Transcription(BaseModel):
  text: str

# Timeseries
class TimeseriesReading(BaseModel):
  ts: str
  value: float
  timeseriesid: str

# Portfolio
class PortfolioModel(BaseModel):
  name: str
  uri: str