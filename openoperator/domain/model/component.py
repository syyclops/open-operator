from pydantic import BaseModel
from typing import Optional

class Component(BaseModel):
  uri: str
  name: str
  installation_date: str
  type_uri: str
  portfolio_name: str
  facility_name: str
  discipline: str
  parent_uri: Optional[str] = None
  description: Optional[str] = None
  space_uri: Optional[str] = None