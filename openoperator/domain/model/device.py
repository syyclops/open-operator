from pydantic import BaseModel
from typing import Optional, List
from .point import Point

class Device(BaseModel):
  uri: str  # https://syyclops.com/{portfolio}/{facility}/device/{device_address}-{device_id}
  device_name: str
  device_id: str
  device_description: Optional[str] = None
  device_address: Optional[str] = None
  object_units: Optional[str] = None
  object_type: Optional[str] = None
  points: List[Point] = []
  template_id: Optional[str] = None

class DeviceCreateParams(BaseModel):
  device_name: str
  device_address: str
  device_id: str
  device_description: Optional[str] = None
  object_units: Optional[str] = None
  object_type: Optional[str] = None
  template_id: Optional[str] = None