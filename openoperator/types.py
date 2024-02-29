from pydantic import BaseModel
from typing import Literal, Optional, List
from typing_extensions import TypedDict

## Document Loader
class DocumentQuery(BaseModel):
  query: str
  limit: int = 15
  document_uri: str = None

class DocumentMetadata(TypedDict, total=False):
  portfolio_uri: str
  facility_uri: str
  document_uri: str
  document_url: str
  filename: str
  filetype: str
  page_number: int

class DocumentMetadataChunk(BaseModel):
  content: str
  metadata: DocumentMetadata

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

# Point
class PointModel(BaseModel):
  uri: str
  object_type: str
  object_index: str
  object_units: str
  timeseriesId: str
  collect_enabled: bool
  object_name: str
  object_description: Optional[str] = None
  value: Optional[float] = None
  ts: Optional[str] = None
  embedding: Optional[List[float]] = None