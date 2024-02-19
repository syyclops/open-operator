from .postgres import Postgres
from typing import List
from openoperator.types import TimeseriesReading

class Timescale:
  def __init__(self, postgres: Postgres) -> None:
    self.postgres = postgres
    collection_name = 'timeseries'
    try:
      with self.postgres.cursor() as cur:
        cur.execute('CREATE EXTENSION IF NOT EXISTS timescaledb') # Create timescaledb extension
        cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{collection_name}\')') # Check if timeseries table exists
        if not cur.fetchone()[0]: cur.execute(f'CREATE TABLE {collection_name} (ts timestamptz NOT NULL, value FLOAT NOT NULL, timeseriesid TEXT NOT NULL)') # Create timeseries table if it doesn't exist
        cur.execute(f'SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = \'{collection_name}\'') # Check if hypertable exists
        if not cur.fetchone(): cur.execute(f'SELECT create_hypertable(\'{collection_name}\', \'ts\')') # Create hypertable if it doesn't exist
        cur.execute(f'SELECT indexname FROM pg_indexes WHERE tablename = \'{collection_name}\' AND indexname = \'{collection_name}_timeseriesid_ts_idx\'') # Check if the table has the timeseriesid index
        if not cur.fetchone(): cur.execute(f'CREATE INDEX {collection_name}_timeseriesid_ts_idx ON {collection_name} (timeseriesid, ts DESC)') # Create the timeseriesid index if it doesn't exist
    except Exception as e:
      raise e
  
  def get_timeseries(self, timeseriesIds: List[str], start_time: str, end_time: str) -> List[dict]:
    ids = ', '.join([f'\'{id}\'' for id in timeseriesIds])
    query = f"SELECT * FROM timeseries WHERE timeseriesid IN ({ids}) AND ts >= %s AND ts <= %s ORDER BY ts ASC"
    try:
      with self.postgres.cursor() as cur:
        cur.execute(query, (start_time, end_time))
        rows = cur.fetchall()
        result = []
        for id in timeseriesIds:
          data = [TimeseriesReading(ts=row[0].isoformat(), value=row[1], timeseriesid=row[2]).model_dump() for row in rows if row[2] == id]
          result.append({'data': data, 'timeseriesid': id})
        return result
    except Exception as e:
      raise e
    
  def get_latest_values(self, timeseriesIds: List[str]) -> List[TimeseriesReading]:
    """
    Get the most recent reading for a list of timeseriesIds. Limit to the last 30 minutes.
    """
    ids = ', '.join([f'\'{id}\'' for id in timeseriesIds])
    query = f"SELECT DISTINCT ON (timeseriesid) * FROM timeseries WHERE timeseriesid IN ({ids}) AND ts >= NOW() - INTERVAL '30 minutes' ORDER BY timeseriesid, ts DESC"
    try:
      with self.postgres.cursor() as cur:
        cur.execute(query)
        return [TimeseriesReading(ts=row[0].isoformat(), value=row[1], timeseriesid=row[2]) for row in cur.fetchall()]
    except Exception as e:
      raise e