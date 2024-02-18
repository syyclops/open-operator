import json
from rdflib import Graph, Namespace, Literal, URIRef, RDF
from rdflib.namespace import XSD
from openoperator.services import Embeddings, Timescale
from uuid import uuid4
class BACnet:
  """
  This class handles the BACnet integration with the knowledge graph.

  It is responsible for:
  - Importing bacnet devices and points
  - Aligning devices with components from the cobie schema
  - Aligning points with components from the brick schema
  """
  def __init__(self, facility, embeddings: Embeddings, timescale: Timescale) -> None:
    self.knowledge_graph = facility.knowledge_graph 
    self.blob_store = facility.blob_store
    self.uri = facility.uri
    self.embeddings = embeddings
    self.timescale = timescale

  def convert_bacnet_data_to_rdf(self, file: bytes) -> Graph:
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

        device_uri = URIRef(self.uri + "/" + bacnet_data['device_address'] + "-" + bacnet_data['device_id'] + "/device/" + bacnet_data['device_id'])
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
          point_uri = URIRef(self.uri + '/' + bacnet_data['device_address'] + '-' + bacnet_data['device_id'] + '/' + bacnet_data['object_type'] + '/' + bacnet_data['object_index'])
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

  def upload_bacnet_data(self, file: bytes):
    """
    This function takes a json file of bacnet data, converts it to rdf and uploads it to the knowledge graph.
    """
    try:
      g = self.convert_bacnet_data_to_rdf(file)
      graph_string = g.serialize(format='turtle', encoding='utf-8').decode()
      unique_id = str(uuid4())
      url = self.blob_store.upload_file(file_content=graph_string.encode(), file_name=f"{unique_id}_bacnet.ttl", file_type="text/turtle")
      self.knowledge_graph.import_rdf_data(url)
      return g
    except Exception as e:
      raise e