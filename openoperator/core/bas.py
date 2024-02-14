import json
from rdflib import Graph, Namespace, Literal, URIRef
from openoperator.services import Embeddings
from uuid import uuid4
import numpy as np
from neo4j.exceptions import Neo4jError
from openoperator.utils import create_uri, dbscan_cluster

class BAS:
  """
  This class handles the integration to the Building Automation System (BAS).

  It is responsible for:
  - Uploading data from BAS to the knowledge graph
  - Converting bacnet data to rdf, and transforming into the brickschema
  - Aligning devices with components from the cobie schema
  """
  def __init__(self, facility, embeddings: Embeddings) -> None:
    self.knowledge_graph = facility.knowledge_graph 
    self.blob_store = facility.blob_store
    self.uri = facility.uri
    self.embeddings = embeddings

  def upload_bacnet_data(self, file: bytes):
    """
    This function takes a json file of bacnet data, converts it to rdf and uploads it to the knowledge graph.
    """
    try:
      # Load the file
      data = json.loads(file)

      # Define namespaces for the graph
      RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
      BACNET = Namespace("http://data.ashrae.org/bacnet/#")
      A = RDF['type']

      g = Graph()
      g.bind("bacnet", BACNET)
      g.bind("rdf", RDF)

      # Loop through the bacnet json file
      for item in data:
        if item['Bacnet Data'] == None:
          continue
        if item['Bacnet Data'] == "{}":
          continue
        bacnet_data = json.loads(item['Bacnet Data'])[0]

        # Check if the necessary keys are in bacnet_data
        if not all(key in bacnet_data for key in ['device_address', 'device_id', 'device_name']):
          print("Missing necessary key in bacnet_data, skipping this item.")
          continue

        if bacnet_data['device_name'] == None or bacnet_data['device_name'] == "":
          continue

        device_uri = URIRef(self.uri + '/device/' + bacnet_data['device_address'] + "-" + bacnet_data['device_id'] + '/' + create_uri(bacnet_data['device_name']))
        # Check if its a bacnet device or a bacnet object
        if bacnet_data['object_type'] == "device":
          # Create the bacnet device and add it to the graph
          g.add((device_uri, A, BACNET.Device))

          # Go through all the bacnet data and add it to the graph
          for key, value in bacnet_data.items():
            if key == "object_type":
              continue
            g.add((device_uri, BACNET[key], Literal(str(value))))
        else:
          # Create the bacnet point and add it to the graph
          point_uri = URIRef(device_uri + '/point/' + bacnet_data['object_type'] + "/" + create_uri(bacnet_data['object_name']) + "/" + bacnet_data['object_index'])
          g.add((point_uri, A, BACNET.Point))

          # Go through all the bacnet data and add it to the graph
          for key, value in bacnet_data.items():
            if key == "object_type":
              continue
            g.add((point_uri, BACNET[key], Literal(str(value))))

            # Create relationship between the device and the point
            g.add((point_uri, BACNET.objectOf, device_uri))

      # Serialize the graph to a file
      graph_string = g.serialize(format='turtle', encoding='utf-8').decode()
      unique_id = str(uuid4())
      url = self.blob_store.upload_file(file_content=graph_string.encode(), file_name=f"{unique_id}_bacnet.ttl", file_type="text/turtle")
      self.knowledge_graph.import_rdf_data(url)
    except Exception as e:
      raise e
        
  def devices(self):
    """
    Get the bacnet devices in the facility.
    """
    query = "MATCH (d:Device) where d.uri starts with $uri RETURN d"
    try:
      with self.knowledge_graph.create_session() as session:
        result = session.run(query, uri=self.uri)
        devices = [record['d'] for record in result.data()]
      return devices
    except Exception as e:
      raise e
        
  def points(self, device_uri: str | None = None):
    """
    Get the bacnet points in the facility or a specific device.
    """
    query = "MATCH (p:Point)"
    if device_uri:
      query += "-[:objectOf]->(d:Device {uri: $device_uri})"
    query += " WHERE p.uri STARTS WITH $uri RETURN p"
    with self.knowledge_graph.create_session() as session:
      result = session.run(query, uri=self.uri, device_uri=device_uri)
      return [record['p'] for record in result.data()]
        
  def vectorize_graph(self):
    """
    For each device and point in the facility, create an embedding and upload it to the graph.
    """
    devices = self.devices()

    texts = [device['device_name'] for device in devices]

    embeddings = self.embeddings.create_embeddings(texts)

    id_vector_pairs = []
    for i, device in enumerate(devices):
      id_vector_pairs.append({
          "id": device['uri'],
          "vector": np.array(embeddings[i].embedding)
      })

    # Upload the vectors to the graph
    query = """UNWIND $id_vector_pairs as pair
                MATCH (n:Device) WHERE n.uri = pair.id
                CALL db.create.setNodeVectorProperty(n, 'embedding', pair.vector)
                RETURN n"""
    try:
      with self.knowledge_graph.create_session() as session:
        session.run(query, id_vector_pairs=id_vector_pairs)
    except Neo4jError as e:
      raise e
    
    points = self.points()
    texts = [point['object_name'] for point in points]

    embeddings = self.embeddings.create_embeddings(texts)

    id_vector_pairs = []
    for i, point in enumerate(points):
      id_vector_pairs.append({
          "id": point['uri'],
          "vector": np.array(embeddings[i].embedding)
      })

    # Upload the vectors to the graph
    query = """UNWIND $id_vector_pairs as pair
                MATCH (n:Point) WHERE n.uri = pair.id
                CALL db.create.setNodeVectorProperty(n, 'embedding', pair.vector)
                RETURN n"""
    
    try:
      with self.knowledge_graph.create_session() as session:
        session.run(query, id_vector_pairs=id_vector_pairs)
    except Neo4jError as e:
      raise e
        
  def cluster_devices(self):
    """
    Cluster the bacnet devices using the embeddings that were created from vectorizing the graph.
    """
    devices = self.devices()

    embeddings = [device['embedding'] for device in devices]
    embeddings = np.vstack(embeddings)

    cluster_assignments = dbscan_cluster(embeddings)

    # Create a dictionary of clusters, with the key being the cluster number and the value being the list of documents and metadata
    clusters = {}
    for i in range(len(cluster_assignments)):
      cluster = cluster_assignments[i]
      if cluster not in clusters:
        clusters[cluster] = []
      clusters[cluster].append(devices[i]['device_name']) 

    return clusters
    
  def cluster_points(self):
    """
    Cluster the bacnet points using the embeddings that were created from vectorizing the graph.
    """
    points = self.points()

    embeddings = [point['embedding'] for point in points]
    embeddings = np.vstack(embeddings)

    cluster_assignments = dbscan_cluster(embeddings)

    # Create a dictionary of clusters, with the key being the cluster number and the value being the list of documents and metadata
    clusters = {}
    for i in range(len(cluster_assignments)):
      cluster = cluster_assignments[i]
      if cluster not in clusters:
        clusters[cluster] = []
      clusters[cluster].append(points[i]['object_name'])
    
    return clusters