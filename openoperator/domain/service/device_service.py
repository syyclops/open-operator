from openoperator.domain.repository import DeviceRepository
from openoperator.domain.model import Device

class DeviceService:
  def __init__(self, device_repository: DeviceRepository):
    self.device_repository = device_repository
  
  def get_devices(self, facility_uri: str) -> list[Device]:
    return self.device_repository.get_devices(facility_uri)
  
  def link_device_to_component(self, device_uri: str, component_uri: str):
    return self.device_repository.link_device_to_component(device_uri, component_uri)