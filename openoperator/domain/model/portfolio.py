from pydantic import BaseModel

class Portfolio(BaseModel):
  uri: str
  name: str