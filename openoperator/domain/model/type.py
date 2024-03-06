from pydantic import BaseModel
from typing import Optional

class Type(BaseModel):
  category_name: str
  name: str
  portfolio_name: str
  facility_name: str
  uri: str
  category_uri: str
  discipline_name: Optional[str] = None
  manufacturer: Optional[str] = None
  manufacturer_uri: Optional[str] = None
  description: Optional[str] = None
  model_number: Optional[str] = None
  replacement_cost: Optional[str] = None
  expected_life: Optional[str] = None
  nominal_length: Optional[str] = None
  nominal_width: Optional[str] = None
  nominal_height: Optional[str] = None
  shape: Optional[str] = None
  size: Optional[int] = None
  color: Optional[str] = None
  finish: Optional[str] = None
  grade: Optional[str] = None
  material: Optional[str] = None
  weight: Optional[str] = None
  warranty_guarantorParts: Optional[str] = None
  warranty_durationParts: Optional[str] = None
  warranty_guarantorLabor: Optional[str] = None
  warranty_durationLabor: Optional[str] = None
  warranty_durationUnit: Optional[str] = None

