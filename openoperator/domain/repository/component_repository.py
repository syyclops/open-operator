from openoperator.infrastructure import KnowledgeGraph
from openoperator.domain.model import Component
from typing import List
from openoperator.domain.model import Portfolio, Facility
from openoperator.domain.repository.facility_repository import FacilityRepository

class ComponentRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg
    self.facility_repository = FacilityRepository(kg)

  def get_component(self, component_uri: str) -> Component:
    with self.kg.create_session() as session:
      result = session.run("MATCH (c:Component {uri: $uri}) RETURN c", uri=component_uri)
      record = result.single()
      if record is None:
        raise ValueError(f"Component {component_uri} not found")
      component_record = record['c']
      return Component(**component_record)

#GET COMPONENT LIST FOR ALL FACILITIES IN A PORTFOLIO
  def list_components(self, portfolio_uri: str) -> list[Component]:
    with self.kg.create_session() as session:
      result = session.run("MATCH (p:Portfolio {uri: $uri}) RETURN p", uri=portfolio_uri)
      data = result.data()
      facilities = self.facility_repository.list_facilities_for_portfolio(portfolio_uri)
      if not facilities:
          raise ValueError("No facilities found for the given portfolio URI")
      for facility in facilities:
          result = session.run("MATCH (f:Facility {uri: $uri})-[:HAS_COMPONENT]->(c:Component) RETURN c", uri=facility.uri)
          data = result.data()
          return ([Component(**c['c']) for c in data])
    
#CREATE COMPONENT     
  def create_component(self, component: Component, space_uri: str) -> Component:
    with self.kg.create_session() as session:
      params = {
            'uri': component.uri,
            'name': component.name,
            'space_uri': component.space_uri,
            'installation_date': component.installation_date,
            'portfolio_name': component.portfolio_name,
            'facility_name': component.facility_name,
            'discipline': component.discipline,
            'space_uri': component.space_uri,
            'description': component.description,
        }
      query = "MATCH (s:Space {uri: $space_uri}) CREATE (c:Component:Resource {name: $name, uri: $uri}) CREATE (c)-[:space]->(s) SET c.name = $name"
      if params['description']:
          query += ", c.description = $description"
      query += " RETURN c"
      result = session.run(query, params)
      record = result.single()
      print("FAAAA", record)
      if record is None:
        raise ValueError(f"Error creating component {component.uri}")

      return Component(**record['c'])

