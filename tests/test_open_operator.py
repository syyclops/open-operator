import unittest
from unittest.mock import Mock 
from openoperator.core import OpenOperator, User
from openoperator.types import PortfolioModel 
from neo4j.exceptions import Neo4jError

class TestOpenOperator(unittest.TestCase):
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
    self.audio = Mock()
    self.operator = OpenOperator(
        self.blob_store,
        self.embeddings,
        self.document_loader,
        self.vector_store,
        self.timescale,
        self.knowledge_graph,
        self.llm,
        self.audio,
        self.base_uri,
        self.api_token_secret
    )
    self.user = User(self.operator, "test@example.com", "password", "Test User")

  def setup_session_mock(self):
    # Create the session mock
    session_mock = Mock()
    # Simulate entering the context
    session_mock.__enter__ = Mock(return_value=session_mock)
    # Simulate exiting the context
    session_mock.__exit__ = Mock(return_value=None)
    # Configure the knowledge_graph to return this session mock
    self.knowledge_graph.create_session.return_value = session_mock
    return session_mock

  def test_create_portfolio(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.single.return_value = True  # Simulate finding a result
    session_mock.run.return_value = mock_query_result

    portfolio = self.operator.create_portfolio(self.user, "Test Portfolio")
    
    # Verify the portfolio's properties
    assert portfolio.uri == "https://openoperator.com/test%20portfolio"
    assert portfolio.user == self.user

    # Assert that create_session was called once
    self.knowledge_graph.create_session.assert_called_once()

    session_query_string = session_mock.run.call_args[0][0]
    # Assert that session.run was called with the expected query
    assert "CREATE (n:Customer:Resource {name: $name, uri: $uri})" in session_query_string
    assert "CREATE (u)-[:HAS_ACCESS_TO]->(n)" in session_query_string
    assert "RETURN n" in session_query_string
    
  def test_create_portfolio_no_result(self):
    session_mock = self.setup_session_mock()
    # Simulate a scenario where the query returns no result
    session_mock.run.return_value.single.return_value = None

    with self.assertRaises(Exception) as context:
      self.operator.create_portfolio(self.user, "Test Portfolio")

    self.assertTrue("Error creating portfolio" in str(context.exception))

  def test_create_portfolio_exception(self):
    session_mock = self.setup_session_mock()
    # Simulate raising a Neo4jError on query execution
    session_mock.run.side_effect = Neo4jError("Simulated database error")

    with self.assertRaises(Exception) as context:
      self.operator.create_portfolio(self.user, "Test Portfolio")

    self.assertTrue("Simulated database error" in str(context.exception))

  def test_portfolios(self):
    session_mock = self.setup_session_mock()
    # Simulate a query result with two records
    session_mock.run.return_value.data.return_value = [
        {"Customer": {"name": "Customer 1", "uri": "https://openoperator.com/customer1"}},
        {"Customer": {"name": "Customer 2", "uri": "https://openoperator.com/customer2"}},
    ]

    portfolios = self.operator.portfolios(self.user)

    # Verify the returned data
    assert portfolios == [
        PortfolioModel(name="Customer 1", uri="https://openoperator.com/customer1"),
        PortfolioModel(name="Customer 2", uri="https://openoperator.com/customer2"),
    ]

    # Assert that create_session was called once
    self.knowledge_graph.create_session.assert_called_once()

    session_query_string = session_mock.run.call_args[0][0]
    # Assert that session.run was called with the expected query
    assert "MATCH (u:User {email: $email})-[:HAS_ACCESS_TO]->(c:Customer) return c as Customer" in session_query_string

  def test_portfolios_no_records(self):
    session_mock = self.setup_session_mock()
    # Simulate a query result with no records
    session_mock.run.return_value.data.return_value = []

    portfolios = self.operator.portfolios(self.user)

    # Verify the returned data
    assert portfolios == []

    # Assert that create_session was called once
    self.knowledge_graph.create_session.assert_called_once()

    session_query_string = session_mock.run.call_args[0][0]
    # Assert that session.run was called with the expected query
    assert "MATCH (u:User {email: $email})-[:HAS_ACCESS_TO]->(c:Customer) return c as Customer" in session_query_string

  def test_portfolios_exception(self):
    session_mock = self.setup_session_mock()
    # Simulate raising a Neo4jError on query execution
    session_mock.run.side_effect = Neo4jError("Simulated database error")

    with self.assertRaises(Exception) as context:
      self.operator.portfolios(self.user)

    self.assertTrue("Simulated database error" in str(context.exception))
        
  def test_chat(self):
    # Mock the portfolio's search_documents method
    self.operator.portfolio = Mock()
    portfolio = self.operator.portfolio(self.user, "https://openoperator.com/portfolio")
    portfolio.search_documents = Mock(return_value="Search result")

    self.llm.chat.return_value = iter(["AI response to search for documents"])

    # Define the messages to simulate user interaction
    messages = [
        {"content": "Search for documents", "role": "user"}
    ]

    # Execute the chat function
    responses = list(self.operator.chat(messages, portfolio))

    # Verify
    self.llm.chat.assert_called_once()  # Ensure the AI chat was called
    self.assertEqual(len(responses), 1)  # Check if there is one response
    self.assertEqual(responses[0], "AI response to search for documents")  # Validate the response content

  def test_chat_with_ai_error(self):
    # Mock the portfolio's search_documents method
    self.operator.portfolio = Mock()
    portfolio = self.operator.portfolio(self.user, "https://openoperator.com/portfolio")
    portfolio.search_documents = Mock(return_value="Search result")

    self.llm.chat.side_effect = Exception("AI error")

    # Define the messages to simulate user interaction
    messages = [
        {"content": "Search for documents", "role": "user"}
    ]

    # Execute the chat function
    with self.assertRaises(Exception) as context:
      list(self.operator.chat(messages, portfolio))

    self.assertTrue("AI error" in str(context.exception))


if __name__ == '__main__':
  unittest.main()