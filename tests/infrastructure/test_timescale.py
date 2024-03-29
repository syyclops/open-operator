import unittest
from unittest.mock import MagicMock, patch 
from openoperator.infrastructure.timescale import Timescale
import datetime

class TestTimescale(unittest.TestCase):
  def setUp(self) -> None:
    self.postgres = MagicMock()
    self.timescale = Timescale(self.postgres)
    super().setUp()

  def test_init(self):
    with patch.object(self.postgres, 'cursor', return_value=MagicMock()) as mock_cursor:
      # Mock the fetchone() calls to return False, simulating that the table, hypertable, and index do not exist
      mock_cursor().__enter__().fetchone.side_effect = [[False], None, None]
      self.timescale.__init__(self.postgres)
      # Assert that execute was called 7 times (for all the possible execute calls)
      self.assertEqual(mock_cursor().__enter__().execute.call_count, 7)

  def test_get_timeseries(self):
    timeseriesIds = ['id1', 'id2']
    start_time = '2022-01-01 00:00:00'
    end_time = '2022-12-31 23:59:59'
    with patch.object(self.postgres, 'cursor', return_value=MagicMock()) as mock_cursor:
      mock_cursor().__enter__().fetchall.return_value = [
        (datetime.datetime(2022, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), 1.0, 'id1'),
        (datetime.datetime(2022, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc), 2.0, 'id2')
      ]
      result = self.timescale.get_timeseries(timeseriesIds, start_time, end_time)
      expected_result = [
        {'data': [{'timeseriesid': 'id1', 'ts': '2022-01-01T00:00:00+00:00', 'value': 1.0}], 'timeseriesid': 'id1'},
        {'data': [{'timeseriesid': 'id2', 'ts': '2022-12-31T23:59:59+00:00', 'value': 2.0}], 'timeseriesid': 'id2'}
      ] 
      self.assertEqual(result, expected_result)
      ids = ', '.join([f'\'{id}\'' for id in timeseriesIds])
      mock_cursor().__enter__().execute.assert_called_with(f"SELECT * FROM timeseries WHERE timeseriesid IN ({ids}) AND ts >= %s AND ts <= %s ORDER BY ts ASC", (start_time, end_time))

if __name__ == '__main__':
  unittest.main()