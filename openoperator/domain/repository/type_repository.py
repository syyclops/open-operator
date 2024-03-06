from openoperator.infrastructure import KnowledgeGraph
from openoperator.domain.model import Type
from typing import List

class TypeRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg
  
#GET TYPES - PORTFOLIO
  def get_types(self, portfolio_uri: str) -> list[Type]:
    with self.kg.create_session() as session:
      result = session.run("MATCH (p:Portfolio {uri: $uri})-[:HAS_TYPE]->(t:Type) RETURN t", uri=portfolio_uri)
      data = result.data()
      if record is None:
        raise ValueError(f"Portfolio {portfolio_uri} not found")
      type_record = record['t']
      return Type(**type_record)

#GET TYPES - FACILITY
  def list_types_facility(self, facility_uris: list[str]) -> list[Type]:
    with self.kg.create_session() as session:
        query = "MATCH (f:Facility)-[:HAS_TYPE]->(t:Type) WHERE f.uri IN $uris RETURN t"
        result = session.run(query, uris=facility_uris)
        data = result.data()
        return [Type(**t['t']) for t in data]
    
#CREATE NEW TYPE
  def create_type(self, type: Type) -> Type:
    with self.kg.create_session() as session:
        params = {
            'facility_uri': facility_uri,
            'uri': component.uri,
            'name': component.name,
            'installation_date': component.installation_date,
            'type_uri': component.type_uri,
            'portfolio_name': component.portfolio_name,
            'facility_name': component.facility_name,
            'discipline': component.discipline,
            'parent_uri': component.parent_uri,
            'space_uri': component.space_uri,
            'description': component.description,
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
            raise ValueError(f"Error creating type {type['uri']}")

        return Type(**record['t'])