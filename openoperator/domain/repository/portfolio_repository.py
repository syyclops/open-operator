from openoperator.infrastructure import KnowledgeGraph
from openoperator.domain.model import Portfolio, Facility
from typing import List

class PortfolioRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg

  def get_portfolio(self, portfolio_uri: str) -> Portfolio:
    with self.kg.create_session() as session:
      result = session.run("MATCH (p:Customer {uri: $uri}) RETURN p", uri=portfolio_uri)
      data = result.data()
      if len(data) == 0:
        raise ValueError(f"Portfolio {portfolio_uri} not found")
      return Portfolio(uri=data[0]['uri'], name=data[0]['name'])
    
  def create_portfolio(self, portfolio: Portfolio, user_email: str) -> Portfolio:
    with self.kg.create_session() as session:
      result = session.run("MATCH (u:User {email: $email}) CREATE (p:Customer:Resource {name: $name, uri: $uri}) CREATE (u)-[:HAS_ACCESS_TO]->(p) RETURN p", name=portfolio.name, uri=portfolio.uri, email=user_email)
      record = result.single()
      if record is None:
        raise ValueError(f"Error creating portfolio {portfolio.uri}")
      return Portfolio(uri=record['p']['uri'], name=record['p']['name'])
    
  def list_portfolios_for_user(self, email: str) -> List[Portfolio]:
    with self.kg.create_session() as session:
      result = session.run("""MATCH (u:User {email: $email})-[:HAS_ACCESS_TO]->(p:Customer) 
                              MATCH (p)-[:HAS_FACILITY]->(f:Facility)
                              with p, collect(f) as facilities
                              RETURN p as portfolio, facilities""", email=email)
      data = result.data()
      portfolios: List[Portfolio] = []
      for record in data:
        portfolio = Portfolio(uri=record['portfolio']['uri'], name=record['portfolio']['name'])
        facilities = [Facility(uri=f['uri'], name=f['name']) for f in record['facilities']]
        portfolio.facilities = facilities
        portfolios.append(portfolio)
      return portfolios