from openoperator.domain.model import Point, PointUpdates
from openoperator.domain.repository import PointRepository
from openoperator.infrastructure import MQTTClient
from typing import List
import time

class PointService:
  def __init__(self, point_repository: PointRepository, mqtt_client: MQTTClient):
    self.point_repository = point_repository
    self.mqtt_client = mqtt_client

  def get_points(self, facility_uri: str, collect_enabled: bool = None, component_uri: str | None = None) -> list[Point]:
    return self.point_repository.get_points(facility_uri=facility_uri, collect_enabled=collect_enabled, component_uri=component_uri)
  
  def get_point(self, point_uri: str) -> Point:
    return self.point_repository.get_point(point_uri=point_uri)
  
  def update_point(self, point_uri: str, updates: PointUpdates, new_brick_class_uri: str | None = None):
    self.point_repository.update_point(point_uri=point_uri, updates=updates, new_brick_class_uri=new_brick_class_uri)

  def get_points_history(self, point_uris: List[str], start_time: str, end_time: str):
    return self.point_repository.points_history(start_time=start_time, end_time=end_time, point_uris=point_uris)
  
  def command_point(self, point_uri: str, command: str):
    point = self.point_repository.get_point(point_uri)
    # Check if its a command point and has mqtt topic
    is_command_point = self.is_command_point(point)
    if is_command_point:
      self.mqtt_client.connect()
      self.mqtt_client.loop_start()
      self.mqtt_client.publish(point.mqtt_topic, command)
      time.sleep(2) # Wait for the message to be sent
      self.mqtt_client.loop_stop()
      self.mqtt_client.disconnect()
    else:
      raise ValueError("Point is not a command point or does not have mqtt topic")

  def is_command_point(self, point: Point) -> bool:
    if point.brick_class:
      if point.brick_class.label == "Command":
        return True
      
      if point.brick_class.parents:
        for parent in point.brick_class.parents:
          if parent.label == "Command":
            return True
          
    return False