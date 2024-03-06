from pydantic import BaseModel
from typing import Optional
from .type import Type
from .portfolio import Portfolio
from .facility import Facility

class Component(BaseModel):
  uri: str
  name: str
  description: Optional[str] = None
  type_name: Optional[Type] = None
  portfolio_name: Optional[Portfolio] = None
  facility_name: Optional[Facility] = None
  #space: Space.name
  installation_date: Optional[str] = None
  discipline: Optional[str] = None
  parent_uri: Optional[str] = None
