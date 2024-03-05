from openoperator.domain.model import Point
from openoperator.domain.repository import PointRepository
from typing import List

class PointService:
  def __init__(self, point_repository: PointRepository):
    self.point_repository = point_repository

  def get_points(self, facility_uri: str, collect_enabled: bool = True, component_uri: str | None = None) -> list[Point]:
    return self.point_repository.get_points(facility_uri=facility_uri, collect_enabled=collect_enabled, component_uri=component_uri)

  def get_points_history(self, point_uris: List[str], start_time: str, end_time: str):
    return self.point_repository.points_history(start_time=start_time, end_time=end_time, point_uris=point_uris)