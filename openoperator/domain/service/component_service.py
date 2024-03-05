from openoperator.domain.repository import ComponentRepository
from openoperator.domain.model import Component
from openoperator.utils import create_uri

class ComponentService:
  def __init__(self, component_repository: ComponentRepository):
    self.component_repository = component_repository

  def get_component(self, component_uri: str) -> Component:
    return self.component_repository.get_component(component_uri)