from openoperator.core.portfolio.facility.point_manager import PointManager
import unittest
from unittest.mock import Mock, patch

class TestPointManager(unittest.TestCase):
  @patch('openoperator.services.knowledge_graph.KnowledgeGraph')
  def setUp(self, mock_knowledge_graph):
    mock_kg = mock_knowledge_graph.return_value
    facility = Mock()
    facility.knowledge_graph = mock_kg
    facility.uri = "https://openoperator.com/exampleCustomer/exampleFacility"
    embeddings = Mock()
    timescale = Mock()
    self.point_manager = PointManager(facility, embeddings, timescale)

  def setup_session_mock(self):
    # Create the session mock
    session_mock = Mock()
    # Simulate entering the context
    session_mock.__enter__ = Mock(return_value=session_mock)
    # Simulate exiting the context
    session_mock.__exit__ = Mock(return_value=None)
    # Configure the knowledge_graph to return this session mock
    self.point_manager.knowledge_graph.create_session.return_value = session_mock
    return session_mock
  
  def test_points_with_device_uri(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        "p": {
          "point_name": "test_point",
          "uri": "https://openoperator.com/facility/point",
          "timeseriesId": "example/example/301:14-3014/analogInput/1"
        }
      },
      {
        "p": {
          "point_name": "test_point2",
          "uri": "https://openoperator.com/facility/point2",
          "timeseriesId": "example/example/301:14-3014/analogInput/2"
        }
      }
    ]
    session_mock.run.return_value = mock_query_result

    mock_reading = Mock()
    mock_reading.timeseriesid = "example/example/301:14-3014/analogInput/1"
    mock_reading.value = 123
    self.point_manager.timescale.get_latest_values.return_value = [mock_reading]

    points = self.point_manager.points(device_uri="https://openoperator.com/facility/device")

    assert len(points) == 2
    assert points[0]['point_name'] == "test_point"
    assert points[0]['uri'] == "https://openoperator.com/facility/point"
    assert points[1]['point_name'] == "test_point2"