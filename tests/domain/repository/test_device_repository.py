from openoperator.domain.repository import DeviceRepository
import unittest
from unittest.mock import Mock, patch

class TestDeviceManager(unittest.TestCase):
  @patch('openoperator.infrastructure.knowledge_graph.KnowledgeGraph')
  def setUp(self, mock_knowledge_graph):
    mock_kg = mock_knowledge_graph.return_value
    self.facility_uri = "https://openoperator.com/exampleCustomer/exampleFacility"
    embeddings = Mock()
    # timescale = Mock()
    blob_store = Mock()
    self.device_repository = DeviceRepository(kg=mock_kg, embeddings=embeddings, blob_store=blob_store)

  def setup_session_mock(self):
    # Create the session mock
    session_mock = Mock()
    # Simulate entering the context
    session_mock.__enter__ = Mock(return_value=session_mock)
    # Simulate exiting the context
    session_mock.__exit__ = Mock(return_value=None)
    # Configure the knowledge_graph to return this session mock
    self.device_repository.kg.create_session.return_value = session_mock
    return session_mock
  
  def test_devices(self):
    session_mock = self.setup_session_mock()
    # Mock the session.run method to simulate a successful query execution
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        "device": {
          "device_name": "test_device",
          "device_id": "test_device_id",
          "object_type": "analogInput",
          "object_name": "test_point",
          "device_description": "test_description",
          "object_description": "test_description",
          "object_index": "1",
          "device_address": "test_address",
          "scrape_interval": "60",
          "object_units": "noUnits",
          "uri": "https://openoperator.com/facility/device",
        },
        "points": [
          {
            "uri": "https://openoperator.com/facility/point",
            "object_type": "analogInput",
            "object_index": "1",
            "object_units": "noUnits",
            "timeseriesId": "example/example/301:14-3014/analogInput/1",
            "collect_enabled": True,
            "object_name": "test_point",
          }
        ]
      },
      {
        "device": {
          "device_name": "test_device2",
          "device_id": "test_device_id2",
          "object_type": "analogInput",
          "object_name": "test_point2",
          "device_description": "test_description2",
          "object_description": "test_description2",
          "object_index": "2",
          "device_address": "test_address2",
          "scrape_interval": "60",
          "object_units": "noUnits",
          "uri": "https://openoperator.com/facility/device2"
        },
        "points": [
          {
            "uri": "https://openoperator.com/facility/point2",
            "object_type": "analogInput",
            "object_index": "1",
            "object_units": "noUnits",
            "timeseriesId": "example/example/301:14-3014/analogInput/1",
            "collect_enabled": True,
            "object_name": "test_point2",
          }
        ]
      }
    ]
    session_mock.run.return_value = mock_query_result

    devices = self.device_repository.get_devices(facility_uri=self.facility_uri)

    assert len(devices) == 2
    assert devices[0].device_name == "test_device"
    assert devices[0].uri == "https://openoperator.com/facility/device"
    assert devices[1].device_name == "test_device2"

  @patch('openoperator.domain.repository.device_repository.DeviceRepository.get_devices')
  def test_vectorize_graph(self, mock_devices):
    mock_devices.return_value = [
      {
        "device_name": "test_device",
        "uri": "https://openoperator.com/facility/device"
      }
    ]
    self.device_repository.embeddings.create_embeddings.return_value = [Mock(embedding=[0.1, 0.2, 0.3])]
    session_mock = self.setup_session_mock()
    self.device_repository.vectorize(facility_uri=self.facility_uri)

    assert self.device_repository.embeddings.create_embeddings.call_count == 1
    self.device_repository.embeddings.create_embeddings.assert_called_with(['test_device'])

    # Check calls to session.run contain the correct Cypher query for devices and points
    device_query_call = [call for call in session_mock.run.call_args_list if "MATCH (n:Device)" in str(call)]
    self.assertTrue(device_query_call, "Device vectors not uploaded correctly.")

  @patch('openoperator.domain.repository.device_repository.DeviceRepository.get_devices')
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

    clusters = self.device_repository.cluster_devices(facility_uri=self.facility_uri)

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
    self.device_repository.link_device_to_component("https://openoperator.com/facility/device", "https://openoperator.com/facility/component")
    session_mock.run.assert_called_once()

  def test_link_bacnet_device_device_not_found(self):
    session_mock = self.setup_session_mock()
    mock_query_result = Mock()
    mock_query_result.single.return_value = None
    session_mock.run.return_value = mock_query_result
    with self.assertRaises(Exception):
      self.device_repository.link_device_to_component("https://openoperator.com/facility/device", "https://openoperator.com/facility/component")