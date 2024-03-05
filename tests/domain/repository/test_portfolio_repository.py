import unittest
from unittest.mock import Mock 
from openoperator.domain.repository import PortfolioRepository
from openoperator.domain.model import Portfolio, Facility
from neo4j.exceptions import Neo4jError

class TestPortfolioRepository(unittest.TestCase):
  def setUp(self):
    self.blob_store = Mock()
    self.embeddings = Mock()
    self.document_loader = Mock()
    self.vector_store = Mock()
    self.knowledge_graph = Mock()
    self.llm = Mock()
    self.base_uri = "https://openoperator.com/"
    self.api_token_secret = "secret"
    self.timescale = Mock()
    self.portfolio_repository = PortfolioRepository(kg=self.knowledge_graph)
    self.user_email = "example@example.com"

  def setup_session_mock(self):
    # Create the session mock
    session_mock = Mock()
    # Simulate entering the context
    session_mock.__enter__ = Mock(return_value=session_mock)
    # Simulate exiting the context
    session_mock.__exit__ = Mock(return_value=None)
    # Configure the knowledge_graph to return this session mock
    self.portfolio_repository.kg.create_session.return_value = session_mock
    return session_mock

  def test_create_portfolio(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.single.return_value = {
      "p": {
        "name": "Test Portfolio",
        "uri": "https://openoperator.com/test%20portfolio"
      }
    }
    session_mock.run.return_value = mock_query_result

    portfolio = self.portfolio_repository.create_portfolio(portfolio=Portfolio(name="Test Portfolio", uri="https://openoperator.com/test%20portfolio"), user_email=self.user_email)
    
    # Verify the portfolio's properties
    assert portfolio.uri == "https://openoperator.com/test%20portfolio"

    # Assert that create_session was called once
    self.portfolio_repository.kg.create_session.assert_called_once()

    session_query_string = session_mock.run.call_args[0][0]
    # Assert that session.run was called with the expected query
    assert "CREATE (p:Customer:Resource {name: $name, uri: $uri})" in session_query_string
    assert "CREATE (u)-[:HAS_ACCESS_TO]->(p)" in session_query_string
    assert "RETURN p" in session_query_string
    
  def test_create_portfolio_no_result(self):
    session_mock = self.setup_session_mock()
    # Simulate a scenario where the query returns no result
    session_mock.run.return_value.single.return_value = None

    with self.assertRaises(Exception) as context:
      self.portfolio_repository.create_portfolio(portfolio=Portfolio(name="Test Portfolio", uri="https://openoperator.com/test%20portfolio"), user_email=self.user_email)

    self.assertTrue("Error creating portfolio" in str(context.exception))

  def test_create_portfolio_exception(self):
    session_mock = self.setup_session_mock()
    # Simulate raising a Neo4jError on query execution
    session_mock.run.side_effect = Neo4jError("Simulated database error")

    with self.assertRaises(Exception) as context:
      self.portfolio_repository.create_portfolio(portfolio=Portfolio(name="Test Portfolio", uri="https://openoperator.com/test%20portfolio"), user_email=self.user_email)

    self.assertTrue("Simulated database error" in str(context.exception))

  def test_portfolios(self):
    session_mock = self.setup_session_mock()
    # Simulate a query result with two records
    session_mock.run.return_value.data.return_value = [
        {
          "portfolio": {"name": "Customer 1", "uri": "https://openoperator.com/customer1"},
          "facilities": [
            {"uri": "https://openoperator.com/customer1/facility1", "name": "Facility 1"},
            {"uri": "https://openoperator.com/customer1/facility2", "name": "Facility 2"}
          ]
         },
        {
          "portfolio": {"name": "Customer 2", "uri": "https://openoperator.com/customer2"}, 
          "facilities": [
            {"uri": "https://openoperator.com/customer2/facility1", "name": "Facility 1"},
            {"uri": "https://openoperator.com/customer2/facility2", "name": "Facility 2"}
          ]
        },
    ]

    portfolios = self.portfolio_repository.list_portfolios_for_user(email=self.user_email)

    # Verify the returned data
    assert portfolios == [
        Portfolio(name="Customer 1", uri="https://openoperator.com/customer1", facilities=[
          Facility(uri="https://openoperator.com/customer1/facility1", name="Facility 1"),
          Facility(uri="https://openoperator.com/customer1/facility2", name="Facility 2")
        ]),
        Portfolio(name="Customer 2", uri="https://openoperator.com/customer2", facilities=[
          Facility(uri="https://openoperator.com/customer2/facility1", name="Facility 1"),
          Facility(uri="https://openoperator.com/customer2/facility2", name="Facility 2")
        ]),
    ]

    # Assert that create_session was called once
    self.portfolio_repository.kg.create_session.assert_called_once()

    session_query_string = session_mock.run.call_args[0][0]
    # Assert that session.run was called with the expected query
    assert "MATCH (u:User {email: $email})-[:HAS_ACCESS_TO]->(p:Customer)" in session_query_string

  def test_portfolios_no_records(self):
    session_mock = self.setup_session_mock()
    # Simulate a query result with no records
    session_mock.run.return_value.data.return_value = []

    portfolios = self.portfolio_repository.list_portfolios_for_user(email=self.user_email)

    # Verify the returned data
    assert portfolios == []

    # Assert that create_session was called once
    self.portfolio_repository.kg.create_session.assert_called_once()

    session_query_string = session_mock.run.call_args[0][0]
    # Assert that session.run was called with the expected query
    assert "MATCH (u:User {email: $email})-[:HAS_ACCESS_TO]->(p:Customer)" in session_query_string

  def test_portfolios_exception(self):
    session_mock = self.setup_session_mock()
    # Simulate raising a Neo4jError on query execution
    session_mock.run.side_effect = Neo4jError("Simulated database error")

    with self.assertRaises(Exception) as context:
      self.portfolio_repository.list_portfolios_for_user(email=self.user_email)

    self.assertTrue("Simulated database error" in str(context.exception))

if __name__ == '__main__':
  unittest.main()