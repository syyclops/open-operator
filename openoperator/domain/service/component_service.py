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

  def create_component(self, component: Component, space_uri: str) -> Component:
    component_uri = f"{space_uri}/component/{create_uri(component.name)}"
    component = Component(
        uri=component_uri, 
        name=component.name, 
        space_uri=component.space_uri,
    )
    return self.component_repository.create_component(component, facility_uri)