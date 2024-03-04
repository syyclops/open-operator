from openoperator.infrastructure import KnowledgeGraph
from ..point import PointManager
import os
import xml.etree.ElementTree as ET
from neo4j.exceptions import Neo4jError

class Device:
  """
  This class represents a network entity, which could be an IoT device, a BACnet device, or any other type of network-connected equipment.
  """
  def __init__(self, device_uri: str, knowledge_graph: KnowledgeGraph, point_manager: PointManager) -> None:
    self.device_uri = device_uri
    self.knowledge_graph = knowledge_graph
    self.point_manager = point_manager

  def details(self):
    query = "MATCH (d:Device {uri: $device_uri}) RETURN d as Device, labels(d) as labels"
    with self.knowledge_graph.create_session() as session:
      result = session.run(query, device_uri=self.device_uri)
      data = result.data()[0]
      return {"details": data['Device'], "labels": data['labels']}
    
  def update(self, new_details: dict) -> None:
    set_clauses = ', '.join([f'{key}: ${key}' for key in new_details.keys()])
    query = f"MATCH (d:Device {{uri: $device_uri}}) SET d += {{{set_clauses}}} RETURN d"
    try:
      with self.knowledge_graph.create_session() as session:
        session.run(query, device_uri=self.device_uri, **new_details)
    except Neo4jError as e:
      raise e

  def graphic(self):
    """
    Get the svg template for the device and update the values of the points in the template.
    """
    device_details = self.details()
    template_id = device_details['details']['template_id']
    if template_id is None: return None
    points = self.point_manager.points(self.device_uri, collect_enabled=True)
    svg_graphic = os.path.join(os.path.dirname(__file__), "svg_templates", f"{template_id}.svg") # Search the device_graphcs directory for the device graphic
    if os.path.exists(svg_graphic):
      tree = ET.parse(svg_graphic)
      root = tree.getroot()
      for point in points:
        name = point.object_name
        element = root.find(f".//*[@id='{name}']")
        if element is not None and point.value is not None:
          element.text = format(point.value, '.2f') + " " + point.object_units
      updated_svg = ET.tostring(root, encoding='unicode')
      return updated_svg