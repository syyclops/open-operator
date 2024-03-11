from openoperator.domain.service import BACnetService
import unittest
from unittest.mock import Mock, patch
import json
from rdflib import Namespace, RDF, URIRef, Literal

class TestBACnet(unittest.TestCase):
  @patch('openoperator.infrastructure.knowledge_graph.KnowledgeGraph')
  def setUp(self, mock_knowledge_graph):
    # mock_kg = mock_knowledge_graph.return_value
    self.facility_uri = "https://openoperator.com/exampleCustomer/exampleFacility"
    # embeddings = Mock()
    # timescale = Mock()
    device_repository = Mock()
    device_repository.blob_store = Mock()
    self.device_repository = device_repository
    self.bacnet_service = BACnetService(device_repository=device_repository)

  def setup_session_mock(self):
    # Create the session mock
    session_mock = Mock()
    # Simulate entering the context
    session_mock.__enter__ = Mock(return_value=session_mock)
    # Simulate exiting the context
    session_mock.__exit__ = Mock(return_value=None)
    # Configure the knowledge_graph to return this session mock
    self.bacnet_service.device_repository.kg.create_session.return_value = session_mock
    return session_mock

  def create_bacnet_json_data(self) -> bytes:
    data = [
      {
        "Name": "example/example/301:14-3014/device/3014",
        "Site": "Example Site",
        "Client": "Example Client",
        "Point Type": "",
        "Collect Enabled": "False",
        "Collect Interval": "",
        "Marker Tags": "",
        "Kv Tags": "[{}]",
        "Bacnet Data": "[{\"device_id\":\"3014\",\"device_name\":\"VAV-D2-37\",\"object_name\":\"VAV-D2-37\",\"object_type\":\"device\",\"object_index\":\"3014\",\"object_units\":\"\",\"present_value\":\"\",\"device_address\":\"301:14\",\"scrape_enabled\":\"False\",\"scrape_interval\":\"0\",\"device_description\":\"\",\"object_description\":\"\"}]",
        "Collect Config": "[{}]",
        "Updated": "2022-07-07 15:22:54.243447",
        "Created": "2022-01-10 22:09:55.493949"
      },
      {
        "Name": "example/example/301:14-3014/analogInput/1",
        "Site": "Example Site",
        "Client": "Example Client",
        "Point Type": "",
        "Collect Enabled": "True",
        "Collect Interval": "300",
        "Marker Tags": "",
        "Kv Tags": "[{}]",
        "Bacnet Data": "[{\"device_id\":\"3014\",\"device_name\":\"VAV-D2-37\",\"object_name\":\"3A14-Space-Co2\",\"object_type\":\"analogInput\",\"object_index\":\"1\",\"object_units\":\"noUnits\",\"present_value\":\"0.0\",\"device_address\":\"301:14\",\"scrape_enabled\":\"False\",\"scrape_interval\":\"0\",\"device_description\":\"\",\"object_description\":\"\"}]",
        "Collect Config": "[{}]",
        "Updated": "2022-07-07 15:22:54.247305",
        "Created": "2022-01-10 22:09:55.502661"
      },
      {
        "Name": "example/example/192.168.1.40-8000/analogValue/22",
        "Site": "Example Site",
        "Client": "Example Client",
        "Point Type": "",
        "Collect Enabled": "True",
        "Collect Interval": "300",
        "Marker Tags": "",
        "Kv Tags": "[{}]",
        "Bacnet Data": "[{\"device_id\":\"8000\",\"device_name\":\"AHU1\",\"object_name\":\"AHU01-DAT-SP1\",\"object_type\":\"analogValue\",\"object_index\":\"22\",\"object_units\":\"degreesFahrenheit\",\"present_value\":\"70.0\",\"device_address\":\"192.168.1.40\",\"scrape_enabled\":\"False\",\"scrape_interval\":\"0\",\"device_description\":\"\",\"object_description\":\"\"}]",
        "Collect Config": "[{}]",
        "Updated": "2022-07-07 15:22:47.873095",
        "Created": "2022-01-10 22:09:56.009211"
      },
    ]
    return bytes(json.dumps(data), 'utf-8')
  
  def test_convert_bacnet_data_to_rdf(self):
    bacnet_data = self.create_bacnet_json_data()
    g = self.bacnet_service.convert_bacnet_data_to_rdf(facility_uri=self.facility_uri, file=bacnet_data)
    
    BACNET = Namespace("http://data.ashrae.org/bacnet/#")
    device_uri = URIRef("https://openoperator.com/exampleCustomer/exampleFacility/device/301:14-3014")
    assert (device_uri, RDF.type, BACNET.Device) in g
    assert (device_uri, BACNET.device_id, Literal("3014")) in g
    assert (device_uri, BACNET.device_name, Literal("VAV-D2-37")) in g
    assert (device_uri, BACNET.device_address, Literal("301:14")) in g

    point_uri = URIRef("https://openoperator.com/exampleCustomer/exampleFacility/point/301:14-3014/analogInput/1")
    assert (point_uri, RDF.type, BACNET.Point) in g
    assert (point_uri, BACNET.objectOf, device_uri) in g
    assert (point_uri, BACNET.object_name, Literal("3A14-Space-Co2")) in g
    assert (point_uri, BACNET.object_type, Literal("analogInput")) in g
    assert(point_uri, BACNET.timeseriesId, Literal("example/example/301:14-3014/analogInput/1")) in g

  def test_convert_bacnet_data_to_rdf_no_data(self):
    bacnet_data = bytes(json.dumps([]), 'utf-8')
    g = self.bacnet_service.convert_bacnet_data_to_rdf(facility_uri=self.facility_uri, file=bacnet_data)
    assert len(g) == 0
  
  def test_convert_bacnet_data_to_rdf_invalid_data(self):
    bacnet_data = bytes(json.dumps([{"invalid": "data"}]), 'utf-8')
    with self.assertRaises(Exception):
      self.bacnet_service.convert_bacnet_data_to_rdf(facility_uri=self.facility_uri, file=bacnet_data)
    
  def test_convert_bacnet_data_to_rdf_missing_keys(self):
    bacnet_data = bytes(json.dumps([{"Bacnet Data": "{}"}]), 'utf-8')
    g = self.bacnet_service.convert_bacnet_data_to_rdf(facility_uri=self.facility_uri, file=bacnet_data)
    assert len(g) == 0
  
  def test_upload_bacnet_data(self):
    bacnet_data = self.create_bacnet_json_data()
    session_mock = self.setup_session_mock()
    mock_query_result = Mock()
    mock_query_result.data.return_value = [
      {
        'terminationStatus': 'OK',
        'triplesLoaded': 1,
        'triplesParsed': 1,
        'namespaces': {},
        'extraInfo': {}
      }
    ]
    session_mock.run.return_value = mock_query_result
    self.bacnet_service.upload_bacnet_data(facility_uri=self.facility_uri, file=bacnet_data)