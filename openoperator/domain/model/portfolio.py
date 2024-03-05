from pydantic import BaseModel
from .facility import Facility
from typing import List

class Portfolio(BaseModel):
  uri: str
  name: str
  facilities: List[Facility] = []