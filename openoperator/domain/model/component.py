from pydantic import BaseModel
from typing import Optional

class Component(BaseModel):
  uri: str
  name: str
  installation_date: Optional[str] = None
  type_uri: Optional[str] = None
  portfolio_name: Optional[str] = None
  facility_name: Optional[str] = None
  discipline: Optional[str] = None
  parent_uri: Optional[str] = None
  description: Optional[str] = None
  space_uri: Optional[str] = None