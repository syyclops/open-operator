from pydantic import BaseModel
from typing import Optional
from .type import Type
from .portfolio import Portfolio
from .facility import Facility
from .space import Space

class Component(BaseModel):
  uri: str
  name: str
  space_uri: str
  description: Optional[str] = None
  type_name: Type = None
  portfolio_name: Portfolio = None
  facility_name: Facility = None
  installation_date: Optional[str] = None
  discipline: Optional[str] = None