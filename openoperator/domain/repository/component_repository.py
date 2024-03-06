from openoperator.infrastructure import KnowledgeGraph
from openoperator.domain.model import Component
from typing import List

class ComponentRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg
  
#GET SINGLE COMPONENT BY URI
  def get_component(self, component_uri: str) -> Component:
    with self.kg.create_session() as session:
      result = session.run("MATCH (c:Component {uri: $uri}) RETURN c", uri=component_uri)
      record = result.single()
      if record is None:
        raise ValueError(f"Component {component_uri} not found")
      component_record = record['c']
      return Component(**component_record)

#GET COMPONENT LIST FOR A FACILITY
  def list_components_for_facility(self, facility_uri: str) -> list[Component]:
    with self.kg.create_session() as session:
      result = session.run("MATCH (f:Facility {uri: $uri})-[:HAS_COMPONENT]->(c:Component) RETURN c", uri=facility_uri)
      data = result.data()
      return [Component(**c['c']) for c in data]
    
#CREATE COMPONENT     
  def create_component(self, component: Component, facility_uri: str) -> Component:
    with self.kg.create_session() as session:
        params = {
            'name': component['name'],
            'installation_date': component.get('installation_date'),
            'type_uri': component.get('type_uri'),
            'portfolio_name': component.get('portfolio_name'),
            'facility_name': component.get('facility_name'),
            'discipline': component.get('discipline'),
            'parent_uri': component.get('parent_uri'),
            'space_uri': component.get('space_uri'),
            'description': component.get('description'),
        }

        query = "MATCH (f:Facility {uri: $facility_uri}) CREATE (c:Component:Resource {name: $name, uri: $uri}) CREATE (f)-[:HAS_COMPONENT]->(c) SET c.name = $name"
        if params['parent_uri']:
            query += ", c.parent_uri = $parent_uri"
        if params['description']:
            query += ", c.description = $description"
        if params['space_uri']:
            query += ", c.space_uri = $space_uri"
        query += " RETURN c"

        result = session.run(query, params)
        record = result.single()
        if record is None:
            raise ValueError(f"Error creating component {component['uri']}")

        # Create the new space relationship
        if component.get('space_uri'):
            session.run(
                "MATCH (c:Component {uri: $uri}) MATCH (s:Space {uri: $space_uri}) CREATE (c)-[:space]->(s)",
                uri=component['uri'], space_uri=component['space_uri']
            )

        # Create the new type relationship
        if component.get('type_uri'):
            session.run(
                "MATCH (c:Component {uri: $uri}) MATCH (t:Type {uri: $type_uri}) CREATE (c)-[:typeName]->(t)",
                uri=component['uri'], type_uri=component['type_uri']
            )

        # Create subcomponent relationship
        if component.get('parent_uri'):
            session.run(
                "MATCH (pc:Component {uri: $parent_uri}) MATCH (sc:Component {uri: $uri}) CREATE (pc)-[:hasSubcomponent]->(sc)",
                uri=component['uri'], parent_uri=component['parent_uri']
            )

        return Component(**record['c'])