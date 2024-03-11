from pydantic import BaseModel
from typing import Optional, List

class BrickClass(BaseModel):
  uri: str
  label: Optional[str] = None
  description: Optional[str] = None
  parents: Optional[List['BrickClass']] = None

BrickClass.model_rebuild() 