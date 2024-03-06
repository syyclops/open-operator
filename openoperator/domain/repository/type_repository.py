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
      record = result.single()
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
  def create_type(self, type: Type, portfolio_uri: str) -> Type:
    with self.kg.create_session() as session:
        params = {
            'portfolio_uri': portfolio_uri,
            'category_name': type.category_name,
            'name': type.name,
            'portfolio_name': type.portfolio_name,
            'facility_name': type.facility_name,
            'uri': type.uri,
            'category_uri': type.category_uri,
        }

        query = "MATCH (p:Portfolio {uri: $portfolio_uri}) CREATE (t:Type:Resource {name: $name, uri: $uri}) CREATE (p)-[:HAS_TYPE]->(t) SET t.name = $name"
        query += " RETURN c"

        result = session.run(query, params)
        record = result.single()
        if record is None:
            raise ValueError(f"Error creating type {type['uri']}")

        return Type(**record['t'])