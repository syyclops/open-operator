from pydantic import BaseModel
from typing import Optional

class Component(BaseModel):
  uri: str
  name: str
  parent_uri: str
  description: str
  installation_date: str
  space_uri: str
  type_uri: str
  portfolio_name: str
  facility_name: str
  discipline: str