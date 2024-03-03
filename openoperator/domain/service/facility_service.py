from openoperator.domain.repository import FacilityRepository
from openoperator.domain.model import Facility
from openoperator.utils import create_uri

class FacilityService:
  def __init__(self, facility_repository: FacilityRepository):
    self.facility_repository = facility_repository

  def get_facility(self, facility_uri: str) -> Facility:
    return self.facility_repository.get_facility(facility_uri)
  
  def list_facilities_for_portfolio(self, portfolio_uri: str) -> list[Facility]:
    return self.facility_repository.list_facilities_for_portfolio(portfolio_uri)
  
  def create_facility(self, name: str, portfolio_uri: str) -> Facility:
    facility_uri = f"{portfolio_uri}/{create_uri(name)}"
    facility = Facility(uri=facility_uri, name=name)
    return self.facility_repository.create_facility(facility, portfolio_uri)