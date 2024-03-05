from pydantic import BaseModel
from typing import Optional

class Facility(BaseModel):
  uri: str
  name: str
  address: Optional[str] = None
  latitude: Optional[float] = None
  longitude: Optional[float] = None