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

#GET COMPONENT LIST FOR A PORTFOLIO AND/OR FACILITY
#include facilityUri and portfolioUri to check for all values
  def list_components(self, portfolio_uri: str) -> list[Component]:
    with self.kg.create_session() as session:
      result = session.run("MATCH (p:Portfolio {uri: $uri}) RETURN p", uri=portfolio_uri)
      data = result.data()
      facilities = self.facility_repository.list_facilities_for_portfolio(portfolio_uri)
      if not facilities:
          raise ValueError("No facilities found for the given portfolio URI")
      for facility in facilities:
          print("Facility URI:", facility.uri)
          result = session.run("MATCH (f:Facility {uri: $uri})-[:HAS_COMPONENT]->(c:Component) RETURN c", uri=facility.uri)
          data = result.data()
          return ([Component(**c['c']) for c in data])
    
#CREATE COMPONENT     
  def create_component(self, component: Component, facility_uri: str) -> Component:
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
            raise ValueError(f"Error creating component {component['uri']}")

        return Component(**record['c'])