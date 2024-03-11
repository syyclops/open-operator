from openoperator.infrastructure import KnowledgeGraph, Timescale
from openoperator.domain.model import Point, PointUpdates, BrickClass, Device
from collections import OrderedDict

class PointRepository:
  def __init__(self, kg: KnowledgeGraph, ts: Timescale):
    self.kg = kg
    self.ts = ts

  def get_points(self, facility_uri: str, component_uri: str | None = None, device_uri: str | None = None, collect_enabled: bool = None) -> list[Point]:
    query = "MATCH (p:Point"
    if collect_enabled is not None:
      query += "{collect_enabled: $collect_enabled}"
    query += ")"
    if device_uri: 
      query += "-[:objectOf]->(d:Device {uri: $device_uri})"
    elif component_uri: 
      query += "-[:objectOf]-(d:Device)-[:isDeviceOf]-(c:Component {uri: $component_uri})"
    query += " OPTIONAL MATCH (p)-[:hasBrickClass]-(b:Class)"
    query += " WHERE p.uri STARTS WITH $uri RETURN p, b as brick_class ORDER BY p.object_name DESC"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, component_uri=component_uri, uri=facility_uri, collect_enabled=collect_enabled, device_uri=device_uri)
        data = result.data()
        points = []
        for record in data:
          point = Point(**record['p'])
          if 'brick_class' in record.keys():
            point.brick_class = record['brick_class']
          points.append(point)

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
    
  def get_point(self, point_uri: str) -> Point:
    query = """MATCH (p:Point {uri: $point_uri})
              OPTIONAL MATCH (p)-[:hasBrickClass]->(b:Class:Resource)
              OPTIONAL MATCH path=(b)-[:SCO*]->(parent:Class)
              WITH p, b, COLLECT(parent) AS parents
              RETURN p, b AS brick_class, parents"""
    try:
      with self.kg.create_session() as session:
        result = session.run(query, point_uri=point_uri)
        data = result.data()
        point = Point(**data[0]['p'])
        if data[0]['brick_class']:
          parents = [BrickClass(**parent) for parent in data[0]['parents']]
          brick_class = BrickClass(**data[0]['brick_class'])
          brick_class.parents = parents
          point.brick_class = brick_class
          
      return point
    except Exception as e:
      raise e
  
  def create_point(self, device: Device, point: Point, brick_class_uri: str | None = None) -> Point:
    query = """
    MATCH (d:Device {uri: $device_uri})
    CREATE (p:Point:Resource $point) 
    MERGE (p)-[:objectOf]->(d)
    """
    if brick_class_uri:
      query += " WITH p MATCH (b:Class {uri: $brick_class_uri}) MERGE (p)-[:hasBrickClass]->(b)"
    query += " RETURN p"
    try:
      with self.kg.create_session() as session:
        result = session.run(query, device_uri=device.uri, point=point.model_dump(), brick_class_uri=brick_class_uri)
        return Point(**result.data()[0]['p'])
    except Exception as e:
      raise e
  
  def update_point(self, point_uri: str, updates: PointUpdates = None, new_brick_class_uri: str = None):
    """
    Update properties of a point and optionally its brick class relationship.

    :param point_uri: The URI of the point to update.
    :param updates: A dictionary of property updates (e.g., {"object_name": "new_name"}).
    :param new_brick_class_uri: Optional. The URI of the new brick class to associate with the point.
    """
    try:
      with self.kg.create_session() as session:
        # Update point properties
        if updates:
          update_props_query = "MATCH (p:Point {uri: $point_uri}) SET "
          update_props_query += ", ".join(f"p.{k} = ${k}" for k in updates.keys())
          session.run(update_props_query, point_uri=point_uri, **updates)

        # Update brick class relationship if specified
        if new_brick_class_uri:
          update_brick_class_query = """
          MATCH (p:Point {uri: $point_uri})
          OPTIONAL MATCH (p)-[r:hasBrickClass]->(:Class)
          DELETE r
          WITH p
          MATCH (b:Class {uri: $new_brick_class_uri})
          MERGE (p)-[:hasBrickClass]->(b)
          """
          session.run(update_brick_class_query, point_uri=point_uri, new_brick_class_uri=new_brick_class_uri)
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