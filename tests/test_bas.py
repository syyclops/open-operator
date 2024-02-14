from openoperator.core import BAS
import unittest
from unittest.mock import Mock

class TestBAS(unittest.TestCase):
  def setUp(self):
    facility = Mock()
    facility.knowledge_graph = Mock()
    facility.uri = "https://openoperator.com/facility"
    embeddings = Mock()
    self.bas = BAS(facility, embeddings)

  def setup_session_mock(self):
    # Create the session mock
    session_mock = Mock()
    # Simulate entering the context
    session_mock.__enter__ = Mock(return_value=session_mock)
    # Simulate exiting the context
    session_mock.__exit__ = Mock(return_value=None)
    # Configure the knowledge_graph to return this session mock
    self.bas.knowledge_graph.create_session.return_value = session_mock
    return session_mock

  def test_devices(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        "d": {
          "device_name": "test_device",
          "uri": "https://openoperator.com/facility/device"
        }
      },
      {
        "d": {
          "device_name": "test_device2",
          "uri": "https://openoperator.com/facility/device2"
        }
      }
    ]
    session_mock.run.return_value = mock_query_result

    devices = self.bas.devices()

    assert len(devices) == 2
    assert devices[0]['device_name'] == "test_device"
    assert devices[0]['uri'] == "https://openoperator.com/facility/device"
    assert devices[1]['device_name'] == "test_device2"
