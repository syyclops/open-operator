import unittest
from unittest.mock import MagicMock, patch 
from openoperator.services.timescale import Timescale

class TestTimescale(unittest.TestCase):
  def setUp(self) -> None:
    self.postgres = MagicMock()
    self.timescale = Timescale(self.postgres)
    super().setUp()

  def test_init(self):
    with patch.object(self.postgres, 'cursor', return_value=MagicMock()) as mock_cursor:
      mock_cursor().__enter__().fetchone.return_value = [False]
      self.timescale.__init__(self.postgres)
      self.assertEqual(mock_cursor().__enter__().execute.call_count, 6)

  def test_get_timeseries(self):
    timeseriesIds = ['id1', 'id2']
    start_time = '2022-01-01 00:00:00'
    end_time = '2022-12-31 23:59:59'
    with patch.object(self.postgres, 'cursor', return_value=MagicMock()) as mock_cursor:
      mock_cursor().__enter__().fetchall.return_value = [('id1', '2022-01-01 00:00:00', 1.0), ('id2', '2022-12-31 23:59:59', 2.0)]
      result = self.timescale.get_timeseries(timeseriesIds, start_time, end_time)
      self.assertEqual(result, [('id1', '2022-01-01 00:00:00', 1.0), ('id2', '2022-12-31 23:59:59', 2.0)])
      mock_cursor().__enter__().execute.assert_called_with(f'SELECT * FROM timeseries WHERE timeseriesid IN ({", ".join(timeseriesIds)}) AND ts >= {start_time} AND ts <= {end_time}')

if __name__ == '__main__':
  unittest.main()