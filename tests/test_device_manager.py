from openoperator.core.portfolio.facility.device_manager import DeviceManager
import unittest
from unittest.mock import Mock, patch

class TestDeviceManager(unittest.TestCase):
  @patch('openoperator.services.knowledge_graph.KnowledgeGraph')
  def setUp(self, mock_knowledge_graph):
    mock_kg = mock_knowledge_graph.return_value
    facility = Mock()
    facility.knowledge_graph = mock_kg
    facility.uri = "https://openoperator.com/exampleCustomer/exampleFacility"
    embeddings = Mock()
    timescale = Mock()
    self.device_manager = DeviceManager(facility, embeddings, timescale)

  def setup_session_mock(self):
    # Create the session mock
    session_mock = Mock()
    # Simulate entering the context
    session_mock.__enter__ = Mock(return_value=session_mock)
    # Simulate exiting the context
    session_mock.__exit__ = Mock(return_value=None)
    # Configure the knowledge_graph to return this session mock
    self.device_manager.knowledge_graph.create_session.return_value = session_mock
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

    devices = self.device_manager.devices()

    assert len(devices) == 2
    assert devices[0]['device_name'] == "test_device"
    assert devices[0]['uri'] == "https://openoperator.com/facility/device"
    assert devices[1]['device_name'] == "test_device2"

  def test_devices_of_component(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        "d": {
          "device_name": "test_device",
          "uri": "https://openoperator.com/facility/device"
        }
      }
    ]
    session_mock.run.return_value = mock_query_result

    devices = self.device_manager.devices("https://openoperator.com/facility/component")

    assert len(devices) == 1
    assert devices[0]['device_name'] == "test_device"
    assert devices[0]['uri'] == "https://openoperator.com/facility/device"

  def test_points(self):
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

     # Mock the get_latest_values method to return a list of mock readings
    mock_reading = Mock()
    mock_reading.timeseriesid = "example/example/301:14-3014/analogInput/1"
    mock_reading.value = 123
    self.device_manager.timescale.get_latest_values.return_value = [mock_reading]

  @patch('openoperator.core.portfolio.facility.device_manager.DeviceManager.devices')
  def test_vectorize_graph(self, mock_devices):
    mock_devices.return_value = [
      {
        "device_name": "test_device",
        "uri": "https://openoperator.com/facility/device"
      }
    ]
    self.device_manager.embeddings.create_embeddings.return_value = [Mock(embedding=[0.1, 0.2, 0.3])]
    session_mock = self.setup_session_mock()
    self.device_manager.vectorize()

    assert self.device_manager.embeddings.create_embeddings.call_count == 1
    self.device_manager.embeddings.create_embeddings.assert_called_with(['test_device'])

    # Check calls to session.run contain the correct Cypher query for devices and points
    device_query_call = [call for call in session_mock.run.call_args_list if "MATCH (n:Device)" in str(call)]
    self.assertTrue(device_query_call, "Device vectors not uploaded correctly.")

  @patch('openoperator.core.portfolio.facility.device_manager.DeviceManager.devices')
  def test_cluster_devices(self, mock_devices):
    mock_devices.return_value = [
      {
        "device_name": "test_device",
        "uri": "https://openoperator.com/facility/device",
        "embedding": [0.0023064255, 0.0023064255, 0.0023064255, 0.0023064255]
      },
      {
        "device_name": "test_device2",
        "uri": "https://openoperator.com/facility/device2",
        "embedding": [0.0023064255, 0.0023064255, 0.0023064255, 0.0023064255]
      },
      {
        "device_name": "test_device3",
        "uri": "https://openoperator.com/facility/device3",
        "embedding": [0.0023064255, 0.0023064255, 0.0023064255, 0.0023064255]
      },
      {
        "device_name": "outlier",
        "uri": "https://openoperator.com/facility/outlier",
        "embedding": [0.1, 0.1, 0.1, 0.1]
      }
    ]

    clusters = self.device_manager.cluster_devices()

    assert len(clusters) == 2
    assert len(clusters[0]) == 3
    assert len(clusters[-1]) == 1
    assert "test_device" in clusters[0]

  def test_link_bacnet_device_to_cobie_component(self):
    session_mock = self.setup_session_mock()
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        "d": {
          "device_name": "test_device",
          "uri": "https://openoperator.com/facility/device"
        },
        "c": {
          "component_name": "test_component",
          "uri": "https://openoperator.com/facility/component"
        }
      }
    ]
    session_mock.run.return_value = mock_query_result
    self.device_manager.link_to_component("https://openoperator.com/facility/device", "https://openoperator.com/facility/component")
    session_mock.run.assert_called_once()

  def test_link_bacnet_device_device_not_found(self):
    session_mock = self.setup_session_mock()
    mock_query_result = Mock()
    mock_query_result.single.return_value = None
    session_mock.run.return_value = mock_query_result
    with self.assertRaises(Exception):
      self.device_manager.link_to_component("https://openoperator.com/facility/device", "https://openoperator.com/facility/component")