from openoperator.domain.model import Device, Point, DeviceCreateParams
from openoperator.infrastructure import KnowledgeGraph, Embeddings, BlobStore
from openoperator.utils import dbscan_cluster
import os
import numpy as np
from uuid import uuid4

class DeviceRepository:
  def __init__(self, kg: KnowledgeGraph, embeddings: Embeddings, blob_store: BlobStore):
    self.kg = kg
    self.embeddings = embeddings
    self.blob_store = blob_store
  
  def get_devices(self, facility_uri: str, component_uri: str | None = None) -> list[Device]:
    query = "MATCH (d:Device) where d.uri starts with $facility_uri OPTIONAL MATCH (d)-[:objectOf]-(p:Point)"
    if component_uri:
      query += " MATCH (d)-[:isDeviceOf]->(c:Component {uri: $component_uri})"
    query += " with d, collect(p) AS points RETURN d as device, points ORDER BY d.device_name DESC"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, facility_uri=facility_uri, component_uri=component_uri)
        data = result.data()
        devices = []
        for record in data:
          device_data = record['device']
          points_data = record['points']
          device = Device(**device_data)
          points = [Point(**point_data) for point_data in points_data]
          device.points = points
          devices.append(device)
        return devices
    except Exception as e:
      raise e
  
  def create_device(self, facility_uri: str, device: DeviceCreateParams) -> Device:
    uri = f"{facility_uri}/device/{device.device_address}-{device.device_id}"
    device = Device(uri=uri, **device.model_dump())
    query = "CREATE (d:Device:Resource $device) RETURN d"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device=device.model_dump())
        data = result.data()
        return Device(**data[0]['d'])
    except Exception as e:
      raise e
    
  def update(self, device_uri: str, new_details: dict) -> None:
    set_clauses = ', '.join([f'{key}: ${key}' for key in new_details.keys()])
    query = f"MATCH (d:Device {{uri: $device_uri}}) SET d += {{{set_clauses}}} RETURN d"
    try:
      with self.kg.create_session() as session:
        session.run(query, device_uri=device_uri, **new_details)
    except Exception as e:
      raise e

  def link_device_to_component(self, device_uri: str, component_uri: str):
    query = "MATCH (d:Device {uri: $device_uri}) MATCH (c:Component {uri: $component_uri}) MERGE (d)-[:isDeviceOf]->(c) RETURN d, c"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device_uri=device_uri, component_uri=component_uri)
        if result.single() is None: raise ValueError("Error linking device to component")
        return "Device linked to component"
    except Exception as e:
      raise e
    
  def get_device_graphic(self, device_uri: str):
    query = "MATCH (d:Device {uri: $device_uri}) return d"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device_uri=device_uri)
        record = result.single()
        if record is None: raise ValueError("Graphic not found")
        template_id = record['d']['template_id']
      svg_graphic = os.path.join(os.path.dirname(__file__), "svg_templates", f"{template_id}.svg") # Search the device_graphcs directory for the device graphic
      if os.path.exists(svg_graphic):
        return svg_graphic
    except Exception as e:
      raise e
    
  def import_to_graph(self, rdf_string: bytes) -> str:
    unique_id = str(uuid4())
    url = self.blob_store.upload_file(file_content=rdf_string.encode(), file_name=f"{unique_id}_cobie.ttl", file_type="text/turtle")
    self.kg.import_rdf_data(url)
    
  def vectorize(self, facility_uri: str):
    """
    For each device in the facility, create an embedding and upload it to the graph.
    """
    devices = self.get_devices(facility_uri)
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
      with self.kg.create_session() as session:
        session.run(query, id_vector_pairs=id_vector_pairs)
    except Exception as e:
      raise e
    
  def cluster_devices(self, facility_uri: str):
    """
    Cluster the bacnet devices using the embeddings that were created from vectorizing the graph.
    """
    devices = self.get_devices(facility_uri)
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