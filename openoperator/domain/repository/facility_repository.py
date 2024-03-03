from openoperator.infastructure.knowledge_graph import KnowledgeGraph
from openoperator.domain.model import Facility

class FacilityRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg
  
  def get_facility(self, facility_uri: str) -> Facility:
    with self.kg.create_session() as session:
      result = session.run("MATCH (f:Facility {uri: $uri}) RETURN f", uri=facility_uri)
      record = result.single()
      if record is None:
        raise ValueError(f"Facility {facility_uri} not found")
      facility_record = record['f']
      return Facility(uri=facility_record['uri'], name=facility_record['name'])
    
  def list_facilities_for_portfolio(self, portfolio_uri: str) -> list[Facility]:
    with self.kg.create_session() as session:
      result = session.run("MATCH (c:Customer {uri: $uri})-[:HAS_FACILITY]->(f:Facility) RETURN f", uri=portfolio_uri)
      data = result.data()
      print(data)
      return [Facility(uri=f['f']['uri'], name=f['f']['name']) for f in data]
    
  def create_facility(self, facility: Facility, portfolio_uri: str) -> Facility:
    with self.kg.create_session() as session:
      result = session.run("MATCH (c:Customer {uri: $portfolio_uri}) CREATE (f:Facility {name: $name, uri: $uri}) CREATE (c)-[:HAS_FACILITY]->(f) RETURN f", name=facility.name, uri=facility.uri, portfolio_uri=portfolio_uri)
      record = result.single()
      if record is None:
        raise ValueError(f"Error creating facility {facility.uri}")
      return Facility(uri=record['f']['uri'], name=record['f']['name'])