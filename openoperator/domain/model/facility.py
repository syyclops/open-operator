from pydantic import BaseModel

class Facility(BaseModel):
  uri: str
  name: str