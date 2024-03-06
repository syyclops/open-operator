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

  def create_component(self, component: Component, facility_uri: str) -> Component:
    component_uri = f"{facility_uri}/component/{create_uri(component.name)}"
    # Assuming 'installation_date', 'type_uri', 'portfolio_name', 'facility_name', and 'discipline' are required fields for Component
    component = Component(
        uri=component_uri, 
        name=component.name, 
        installation_date=component.installation_date, 
        type_uri=component.type_uri, 
        portfolio_name=component.portfolio_name, 
        facility_name=component.facility_name, 
        discipline=component.discipline,
    )
    return self.component_repository.create_component(component, facility_uri)