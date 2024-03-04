from openoperator.domain.model import Device, Point
from openoperator.infrastructure import KnowledgeGraph, Embeddings

class DeviceRepository:
  def __init__(self, kg: KnowledgeGraph, embeddings: Embeddings):
    self.kg = kg
    self.embeddings = embeddings
  
  def get_devices(self, facility_uri: str) -> list[Device]:
    query = "MATCH (d:Device)-[:objectOf]-(p:Point) where d.uri starts with $facility_uri with d, collect(p) AS points RETURN d as device, points"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, facility_uri=facility_uri)
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

  def link_device_to_component(self, device_uri: str, component_uri: str):
    query = """MATCH (d:Device {uri: $device_uri}) MATCH (c:Component {uri: $component_uri}) MERGE (d)-[:isDeviceOf]->(c) RETURN d, c"""
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device_uri=device_uri, component_uri=component_uri)
        if result.single() is None: raise ValueError("Error linking device to component")
        return "Device linked to component"
    except Exception as e:
      raise e