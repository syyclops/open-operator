from pydantic import BaseModel
from typing import Optional, List
from .point import Point

class Device(BaseModel):
  device_name: str
  device_id: str
  object_type: str
  object_name: str
  device_description: str
  object_description: str
  object_index: str
  device_address: str
  scrape_interval: str
  object_units: str
  uri: str
  points: List[Point] = []
  template_id: Optional[str] = None