from openoperator.infrastructure import KnowledgeGraph, Timescale
from openoperator.domain.model import Point
from collections import OrderedDict

class PointRepository:
  def __init__(self, kg: KnowledgeGraph, ts: Timescale):
    self.kg = kg
    self.ts = ts

  def get_points(self, facility_uri: str, component_uri: str | None = None, device_uri: str | None = None, collect_enabled: bool = True) -> list[Point]:
    query = "MATCH (p:Point {collect_enabled: $collect_enabled})"
    if device_uri: 
      query += "-[:objectOf]->(d:Device {uri: $device_uri})"
    elif component_uri: 
      query += "-[:objectOf]-(d:Device)-[:isDeviceOf]-(c:Component {uri: $component_uri})"
    query += " WHERE p.uri STARTS WITH $uri RETURN p ORDER BY p.object_name"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, component_uri=component_uri, uri=facility_uri, collect_enabled=collect_enabled, device_uri=device_uri)
        points = [Point(**record['p']) for record in result.data()]

      ids = [point.timeseriesId for point in points]
      if len(ids) > 0:
        readings = self.ts.get_latest_values(ids)
        readings_dict = OrderedDict((reading.timeseriesid, {"value": reading.value, "ts": reading.ts}) for reading in readings)

        for point in points:
          if point.timeseriesId in readings_dict:
            point.value = readings_dict[point.timeseriesId]['value']
            point.ts = readings_dict[point.timeseriesId]['ts']
        return points
    except Exception as e:
      raise e
    
  def points_history(self, start_time: str, end_time: str, point_uris: list[str]):
    query = "MATCH (p:Point) WHERE p.uri in $point_uris RETURN p"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, point_uris=point_uris)
        points = [Point(**record['p']) for record in result.data()]

      points = [point.model_dump() for point in points]
      ids = []
      for point in points: 
        point.pop('embedding', None)
        ids.append(point['timeseriesId'])

      data = self.ts.get_timeseries(ids, start_time, end_time)
      data_dict = {item['timeseriesid']: item['data'] for item in data}

      for point in points:
        point['data'] = data_dict.get(point['timeseriesId'], [])

      # Group points by object_units
      grouped_points = {}
      for point in points:
        object_unit = point['object_units']
        if object_unit not in grouped_points:
          grouped_points[object_unit] = []
        grouped_points[object_unit].append(point)
    except Exception as e:
      raise e

    # Convert the dictionary to a list of groups
    grouped_points_list = [{'object_unit': k, 'points': v} for k, v in grouped_points.items()]

    return grouped_points_list