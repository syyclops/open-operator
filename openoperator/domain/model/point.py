from pydantic import BaseModel
from typing import Optional, List

class PointReading(BaseModel):
  ts: str
  value: float
  timeseriesid: str

class Point(BaseModel):
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