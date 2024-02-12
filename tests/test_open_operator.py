import unittest
from unittest.mock import Mock, patch
from openoperator.core import OpenOperator, User
from neo4j.exceptions import Neo4jError

class TestOpenOperator(unittest.TestCase):
    def setUp(self):
        self.blob_store = Mock()
        self.embeddings = Mock()
        self.document_loader = Mock()
        self.vector_store = Mock()
        self.knowledge_graph = Mock()
        self.ai = Mock()
        self.base_uri = "https://openoperator.com/"
        self.api_token_secret = "secret"
        self.operator = OpenOperator(
            self.blob_store,
            self.embeddings,
            self.document_loader,
            self.vector_store,
            self.knowledge_graph,
            self.ai,
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

        self.assertTrue("Error creating portfolio: Simulated database error" in str(context.exception))

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
            {"name": "Customer 1", "uri": "https://openoperator.com/customer1"},
            {"name": "Customer 2", "uri": "https://openoperator.com/customer2"},
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

        self.assertTrue("Error fetching portfolios: Simulated database error" in str(context.exception))
        


if __name__ == '__main__':
    unittest.main()