import os
import psycopg

class Postgres():
  def __init__(self, connection_string: str | None = None) -> None:
    if connection_string is None:
      connection_string = os.environ['POSTGRES_CONNECTION_STRING']

      self.conn = psycopg.connect(connection_string)

  def cursor(self):
    return self.conn.cursor()