from pydantic import BaseModel
from typing import Optional

class BrickClass(BaseModel):
  uri: str
  label: str
  description: Optional[str] = None