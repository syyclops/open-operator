from openoperator.domain.model import Point, PointUpdates, PointCreateParams
from openoperator.domain.repository import PointRepository, DeviceRepository
from openoperator.infrastructure import MQTTClient
from typing import List
import time
from uuid import uuid4
import threading
import json

class PointService:
  def __init__(self, point_repository: PointRepository, device_repository: DeviceRepository, mqtt_client: MQTTClient):
    self.point_repository = point_repository
    self.device_repository = device_repository
    self.mqtt_client = mqtt_client

  def get_points(self, facility_uri: str, collect_enabled: bool = None, component_uri: str | None = None) -> list[Point]:
    return self.point_repository.get_points(facility_uri=facility_uri, collect_enabled=collect_enabled, component_uri=component_uri)
  
  def get_point(self, point_uri: str) -> Point:
    return self.point_repository.get_point(point_uri=point_uri)
  
  def create_point(self, facility_uri: str, device_uri: str, point: PointCreateParams, brick_class_uri: str | None = None) -> Point:
    device = self.device_repository.get_device(device_uri)
    point_uri = f"{facility_uri}/point/{str(uuid4())}"
    point = Point(uri=point_uri, **point.model_dump())
    return self.point_repository.create_point(device=device, point=point, brick_class_uri=brick_class_uri)
  
  def update_point(self, point_uri: str, updates: PointUpdates, new_brick_class_uri: str | None = None):
    self.point_repository.update_point(point_uri=point_uri, updates=updates, new_brick_class_uri=new_brick_class_uri)

  def get_points_history(self, point_uris: List[str], start_time: str, end_time: str):
    return self.point_repository.points_history(start_time=start_time, end_time=end_time, point_uris=point_uris)
  
  def get_live_reading(self, point_uri: str):
    """
    Connects to the mqtt broker and listens to the topic of the point.
    """
    try:
      point = self.point_repository.get_point(point_uri)
      if point.mqtt_topic:
        received_event = threading.Event()
        value = None

        def on_message(client, userdata, message):
          nonlocal value
          message_payload = message.payload.decode()
          value = json.loads(message_payload)
          value = value["output"]
          received_event.set()

        self.mqtt_client.client.on_message = on_message
        try:
          self.mqtt_client.connect()
          self.mqtt_client.loop_start()
          self.mqtt_client.subscribe(point.mqtt_topic)
          received_event.wait()  # Wait until a message is received
        finally:
          self.mqtt_client.loop_stop()
          self.mqtt_client.disconnect()
        return value
    except Exception as e:
      raise e
    
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