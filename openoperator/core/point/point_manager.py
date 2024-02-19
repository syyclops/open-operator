from openoperator.services import Embeddings, Timescale
import numpy as np
from openoperator.utils import dbscan_cluster
from neo4j.exceptions import Neo4jError

class PointManager:
  def __init__(self, facility, embeddings: Embeddings, timescale: Timescale) -> None:
    self.knowledge_graph = facility.knowledge_graph 
    self.blob_store = facility.blob_store
    self.uri = facility.uri
    self.embeddings = embeddings
    self.timescale = timescale

  def points(self, device_uri: str | None = None, collect_enabled: bool = True, component_uri: str | None = None):
    """
    Get the points in the facility or a specific device. Then fetch their latest values. 
    """
    query = "MATCH (p:Point"
    if collect_enabled: query += " {collect_enabled: true}"
    query += ")"
    if device_uri: 
      query += "-[:objectOf]->(d:Device {uri: $device_uri})"
    elif component_uri: 
      query += "-[:objectOf]-(d:Device)-[:isDeviceOf]-(c:Component {uri: $component_uri})"
    query += " WHERE p.uri STARTS WITH $uri RETURN p"
    with self.knowledge_graph.create_session() as session:
      result = session.run(query, uri=self.uri, device_uri=device_uri, component_uri=component_uri)
      points = [record['p'] for record in result.data()]
    
    ids = [point['timeseriesId'] for point in points]
    readings = self.timescale.get_latest_values(ids)
    readings_dict = {reading.timeseriesid: {"value": reading.value, "ts": reading.ts} for reading in readings}

    for point in points:
      if point['timeseriesId'] in readings_dict:
        point['value'] = readings_dict[point['timeseriesId']]['value']
        point['ts'] = readings_dict[point['timeseriesId']]['ts']
    return points
  
  def cluster_points(self):
    """
    Cluster the points using the embeddings that were created from vectorizing the graph.
    """
    points = self.points()
    embeddings = [point['embedding'] for point in points]
    embeddings = np.vstack(embeddings)
    cluster_assignments = dbscan_cluster(embeddings)

    clusters = {} # Create a dictionary of clusters, with the key being the cluster number and the value being the list of documents and metadata
    for i in range(len(cluster_assignments)):
      cluster = cluster_assignments[i]
      if cluster not in clusters: clusters[cluster] = []
      clusters[cluster].append(points[i]['object_name'])
    
    return clusters
  
  def vectorize_graph(self):
    """
    For each point in the facility, create an embedding and upload it to the graph.
    """
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