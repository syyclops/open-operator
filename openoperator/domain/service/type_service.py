from openoperator.domain.repository import TypeRepository
from openoperator.domain.model import Type
from openoperator.utils import create_uri

class TypeService:
  def __init__(self, type_repository: TypeRepository):
    self.type_repository = type_repository

  def get_types(self, portfolio_uri: str) -> list[Type]:
    return self.type_repository.get_types(portfolio_uri)

  def list_types_facility(self, facility_uris: list[str]) -> list[Type]:
      return self.type_repository.list_types_facility(facility_uris)

  def create_type(self, type: Type, facillity_uri) -> Type:
    type_uri = f"{facillity_uri}/type/{create_uri(type.name)}"
    type = Type(
        uri=type_uri, 
        name=type.name, 
        category_name= type.category_name,
        portfolio_name=type.portfolio_name,
        facility_name=type.facility_name, 
        category_uri= type.category_uri,
    )
    return self.type_repository.create_type(type, portfolio_uri)