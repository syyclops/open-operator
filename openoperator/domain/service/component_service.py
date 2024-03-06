from openoperator.domain.repository import ComponentRepository
from openoperator.domain.model import Component
from openoperator.utils import create_uri

class ComponentService:
  def __init__(self, component_repository: ComponentRepository):
    self.component_repository = component_repository

  def get_component(self, component_uri: str) -> Component:
    return self.component_repository.get_component(component_uri)

  def list_components_for_facility(self, facility_uri: str) -> list[Component]:
      return self.component_repository.list_components_for_facility(facility_uri)

  def create_component(self, component: Component, facility_uri: str) -> Component:
    component_uri = f"{facility_uri}/{create_uri(name)}"
    component = Component(uri=component_uri, name=name)
    return self.component_repository.create_component(component, facility_uri)