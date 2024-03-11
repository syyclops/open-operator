import json
from rdflib import Graph, Namespace, Literal, URIRef, RDF
from rdflib.namespace import XSD
from openoperator.domain.repository import DeviceRepository

class BACnetService:
  """
  This class handles the BACnet integration with the knowledge graph.

  It is responsible for:
  - Importing bacnet devices and points
  - Aligning devices with components from the cobie schema
  - Aligning points with components from the brick schema
  """
  def __init__(self, device_repository: DeviceRepository) -> None:
    self.device_repository = device_repository

  def convert_bacnet_data_to_rdf(self, facility_uri: str, file: bytes) -> Graph:
    try:
      # Load the file
      data = json.loads(file)
      BACNET = Namespace("http://data.ashrae.org/bacnet/#")
      A = RDF.type
      g = Graph()
      g.bind("bacnet", BACNET)
      g.bind("rdf", RDF)

      # Loop through the bacnet json file
      for item in data:
        if item['Bacnet Data'] == None or item['Bacnet Data'] == "{}": continue
        name = item['Name']
        collect_enabled = item['Collect Enabled']
        bacnet_data = json.loads(item['Bacnet Data'])[0]

        # Check if the necessary keys are in bacnet_data
        if not all(key in bacnet_data for key in ['device_address', 'device_id', 'device_name']):
          print("Missing necessary key in bacnet_data, skipping this item.")
          continue

        if bacnet_data['device_name'] == None or bacnet_data['device_name'] == "":
          continue

        device_uri = URIRef(facility_uri + "/device/" + bacnet_data['device_address'] + "-" + bacnet_data['device_id'])
        # Check if its a bacnet device or a bacnet object
        if bacnet_data['object_type'] == "device":
          # Create the bacnet device and add it to the graph
          g.add((device_uri, A, BACNET.Device))

          # Go through all the bacnet data and add it to the graph
          for key, value in bacnet_data.items():
            if key == "present_value" or key == "scrape_enabled": continue
            g.add((device_uri, BACNET[key], Literal(str(value))))
        else:
          # Create the bacnet point and add it to the graph
          point_uri = URIRef(facility_uri + '/point/' + bacnet_data['device_address'] + '-' + bacnet_data['device_id'] + '/' + bacnet_data['object_type'] + '/' + bacnet_data['object_index'])
          g.add((point_uri, A, BACNET.Point))
          g.add((point_uri, BACNET.timeseriesId, Literal(name)))
          g.add((point_uri, BACNET.objectOf, device_uri)) # Create relationship between the device and the point

          # Go through all the bacnet data and add it to the graph
          for key, value in bacnet_data.items():
            if key == "present_value" or key == "scrape_enabled": continue
            g.add((point_uri, BACNET[key], Literal(str(value))))

          g.add((point_uri, BACNET.collect_enabled, Literal(collect_enabled, datatype=XSD.boolean)))
      return g
    except Exception as e:
      raise e

  def upload_bacnet_data(self, facility_uri: str, file: bytes):
    """
    This function takes a json file of bacnet data, converts it to rdf and uploads it to the knowledge graph.
    """
    try:
      g = self.convert_bacnet_data_to_rdf(facility_uri, file)
      graph_string = g.serialize(format='turtle', encoding='utf-8').decode()
      self.device_repository.import_to_graph(graph_string)
    except Exception as e:
      raise e