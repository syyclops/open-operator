from .postgres import Postgres
from typing import List

class Timescale:
  def __init__(self, postgres: Postgres) -> None:
    self.postgres = postgres
    collection_name = 'timeseries'
    try:
      self.postgres.conn.autocommit = True
      with self.postgres.cursor() as cur:
        cur.execute('CREATE EXTENSION IF NOT EXISTS timescaledb') # Create timescaledb extension
        cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{collection_name}\')') # Check if table exists
        exists = cur.fetchone()[0]
        if not exists:
          cur.execute(f'CREATE TABLE {collection_name} (ts timestamptz NOT NULL, value FLOAT NOT NULL, timeseriesid TEXT NOT NULL)')
        cur.execute(f'SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = \'{collection_name}\'') # Check if hypertable exists
        fetch_result = cur.fetchone()
        exists = fetch_result[0] if fetch_result is not None else None
        if not exists:
          cur.execute(f'SELECT create_hypertable(\'{collection_name}\', \'ts\')')
        # Check if the table has the timeseriesid index
        cur.execute(f'SELECT indexname FROM pg_indexes WHERE tablename = \'{collection_name}\' AND indexname = \'{collection_name}_timeseriesid_ts_idx\'')
        exists = cur.fetchone()
        if not exists:
          cur.execute(f'CREATE INDEX {collection_name}_timeseriesid_ts_idx ON {collection_name} (timeseriesid, ts DESC)')

    except Exception as e:
      raise e
  
  def get_timeseries(self, timeseriesIds: List[str], start_time: str, end_time: str):
    ids = ', '.join([f'\'{id}\'' for id in timeseriesIds])
    query = f"SELECT * FROM timeseries WHERE timeseriesid IN ({ids}) AND ts >= '{start_time}' AND ts <= '{end_time}'"
    try:
      with self.postgres.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()
    except Exception as e:
      raise e