from pydantic import BaseModel
from .facility import Facility

class Portfolio(BaseModel):
  uri: str
  name: str
  facilities: list[Facility] = []