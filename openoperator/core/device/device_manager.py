from openoperator.services import Embeddings, Timescale
from typing import List
from neo4j.exceptions import Neo4jError
import numpy as np
from openoperator.utils import dbscan_cluster

class DeviceManager:
  """
  This class handles the Devices of a facility
  """
  def __init__(self, facility, embeddings: Embeddings, timescale: Timescale) -> None:
    self.knowledge_graph = facility.knowledge_graph 
    self.blob_store = facility.blob_store
    self.uri = facility.uri
    self.embeddings = embeddings
    self.timescale = timescale

  def devices(self, component_uri: str | None = None, brick_class: str | None = None):
    """
    Get the devices in the facility.
    """
    query = "MATCH (d:Device"
    if brick_class: query += f":brick_{brick_class}"
    query += ") where d.uri starts with $uri"
    if component_uri:
      query += " MATCH (d)-[:isDeviceOf]->(c:Component {uri: $component_uri})"
    query += " RETURN d"
    try:
      with self.knowledge_graph.create_session() as session:
        result = session.run(query, uri=self.uri, component_uri=component_uri)
        devices = [record['d'] for record in result.data()]
      return devices
    except Exception as e:
      raise e
    
  def assign_brick_class(self, uris: List[str], brick_class: str):
    """
    Assign a brick class to a device. Add it as a label to the node.
    """
    query = f"MATCH (n) WHERE n.uri IN $uris SET n:brick_{brick_class} RETURN n"
    try:
      with self.knowledge_graph.create_session() as session:
        session.run(query, uris=uris)
    except Neo4jError as e:
      raise e
    
  def vectorize(self):
    """
    For each device in the facility, create an embedding and upload it to the graph.
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
  
  def link_to_component(self, device_uri: str, component_uri: str):
    """
    Link a device to a component in the facility.
    """
    query = """MATCH (d:Device {uri: $device_uri}) MATCH (c:Component {uri: $component_uri}) MERGE (d)-[:isDeviceOf]->(c) RETURN d, c"""
    try:
      with self.knowledge_graph.create_session() as session:
        result = session.run(query, device_uri=device_uri, component_uri=component_uri)
        if result.single() is None: raise ValueError("Error linking device to component")
        return "Device linked to component"
    except Neo4jError as e:
      raise e