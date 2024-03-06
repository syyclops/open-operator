from pydantic import BaseModel
from typing import Optional
from .type import Type
from .portfolio import Portfolio
from .facility import Facility

class Space(BaseModel):
  uri: str
  name: str
  #category: Category
  description: Optional[str] = None
  extIdentifier: Optional[str] = None
  extObjectDatatype: Optional[str] = None
  extSystem: Optional[str] = None
  floorName: Optional[str] = None
  grossArea: Optional[str] = None
  netArea: Optional[str] = None
  roomTag: Optional[str] = None
  usableHeight: Optional[str] = None
  facility_uri: Optional[Facility] = None