from openoperator.services import KnowledgeGraph
from ..point import PointManager
import os
import xml.etree.ElementTree as ET

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

  def graphic(self):
    device_details = self.details()
    brick_class = next((label.replace("brick_", "") for label in device_details['labels'] if "brick_" in label), None)
    if brick_class is None:
      return None
    points = self.point_manager.points(self.device_uri, collect_enabled=True)
    # Search the device_graphcs directory for the device graphic
    svg_graphic = os.path.join(os.path.dirname(__file__), "device_graphics", f"{brick_class}.svg")
    if os.path.exists(svg_graphic):
      tree = ET.parse(svg_graphic)
      root = tree.getroot()
      for point in points:
        name = point['object_name']
        element = root.find(f".//*[@id='{name}']")
        if element is not None and "value" in point:
          element.text += format(point['value'], '.2f')
      updated_svg = ET.tostring(root, encoding='unicode')
      return updated_svg