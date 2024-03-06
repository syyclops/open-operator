from pydantic import BaseModel
from typing import Optional

class Component(BaseModel):
  uri: str
  name: str
  installation_date: Optional[str]
  type_uri: Optional[str]
  portfolio_name: Optional[str]
  facility_name: Optional[str]
  discipline: Optional[str]
  parent_uri: Optional[str] = None
  description: Optional[str] = None
  space_uri: Optional[str] = None