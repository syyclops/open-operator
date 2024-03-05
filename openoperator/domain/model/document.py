from pydantic import BaseModel
from typing import Optional, Literal
from typing_extensions import TypedDict

class DocumentQuery(BaseModel):
  portfolio_uri: str
  query: str
  limit: int = 25
  facility_uri: Optional[str] = None
  document_uri: Optional[str] = None

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

class Document(BaseModel):
  name: str
  uri: str
  url: str
  extractionStatus: Optional[Literal['pending', 'success', 'failed']] = None
  thumbnailUrl: Optional[str] = None