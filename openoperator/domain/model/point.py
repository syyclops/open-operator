from pydantic import BaseModel
from typing import Optional, List
from typing_extensions import TypedDict 
from .brick_class import BrickClass

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
  brick_class: Optional[BrickClass] = None
  mqtt_topic: Optional[str] = None

class PointUpdates(TypedDict, total=False):
  """This is used to update a point's properties."""
  object_name: Optional[str]
  object_description: Optional[str]
  mqtt_topic: Optional[str]
  object_type: Optional[str]
  object_index: Optional[str]
  timeseriesId: Optional[str]