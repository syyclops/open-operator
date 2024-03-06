from openoperator.domain.repository import ComponentRepository
from openoperator.domain.model import Component
from openoperator.utils import create_uri

class ComponentService:
  def __init__(self, component_repository: ComponentRepository):
    self.component_repository = component_repository

  def get_component(self, component_uri: str) -> Component:
    return self.component_repository.get_component(component_uri)

  def list_components(self, portfolio_uri: str) -> list[Component]:
      return self.component_repository.list_components(portfolio_uri)

  def create_component(self, name: str, facility_uri: str, space_uri:str) -> Component:
    component_uri = f"{facility_uri}/component/{create_uri(name)}"
    component = Component(
        uri=component_uri, 
        name=name, 
        space_uri=space_uri,
    )
    return self.component_repository.create_component(component, space_uri)