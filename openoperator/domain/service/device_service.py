from openoperator.domain.repository import DeviceRepository, PointRepository
from openoperator.domain.model import Device, DeviceCreateParams
import xml.etree.ElementTree as ET

class DeviceService:
  def __init__(self, device_repository: DeviceRepository, point_repository: PointRepository):
    self.device_repository = device_repository
    self.point_repository = point_repository
  
  def get_devices(self, facility_uri: str, component_uri: str | None = None) -> list[Device]:
    return self.device_repository.get_devices(facility_uri, component_uri)
  
  def create_device(self, facility_uri: str, device: DeviceCreateParams) -> Device:
    return self.device_repository.create_device(facility_uri=facility_uri, device=device)

  def update(self, device_uri: str, new_details: dict) -> None:
    return self.device_repository.update(device_uri, new_details)
  
  def link_device_to_component(self, device_uri: str, component_uri: str):
    return self.device_repository.link_device_to_component(device_uri, component_uri)
  
  def get_device_graphic(self, facility_uri: str, device_uri: str):
    graphic = self.device_repository.get_device_graphic(device_uri)
    if graphic is not None:
      points = self.point_repository.get_points(facility_uri=facility_uri, device_uri=device_uri)
      tree = ET.parse(graphic)
      root = tree.getroot()
      for point in points:
        name = point.object_name
        element = root.find(f".//*[@id='{name}']")
        if element is not None and point.value is not None:
          element.text = format(point.value, '.2f') + " " + point.object_units
      updated_svg = ET.tostring(root, encoding='unicode')
      return updated_svg
    return None