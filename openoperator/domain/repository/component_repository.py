from openoperator.infrastructure import KnowledgeGraph
from openoperator.domain.model import Component

class ComponentRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg
  
  def get_component(self, component_uri: str) -> Component:
    with self.kg.create_session() as session:
      result = session.run("MATCH (c:Component {uri: $uri}) RETURN c", uri=component_uri)
      record = result.single()
      if record is None:
        raise ValueError(f"Component {component_uri} not found")
      component_record = record['c']
      return Component(**component_record)