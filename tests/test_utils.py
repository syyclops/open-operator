import pytest
from urllib.parse import quote
import numpy as np
from openoperator.utils import split_string_with_limit, create_uri, dbscan_cluster

# Mock encoder for testing split_string_with_limit
class MockEncoder:
  def encode(self, text):
    return text.split()

  def decode(self, tokens):
    return ' '.join(tokens)

@pytest.mark.parametrize("text,limit,expected_parts", [
  ("This is a test string for splitting.", 4, ["This is a test", "string for splitting."]),
  ("OneTwoThreeFourFive", 1, ["OneTwoThreeFourFive"]),  # Test with no spaces
  ("", 10, []),  # Test with empty string
])
def test_split_string_with_limit(text, limit, expected_parts):
  encoder = MockEncoder()
  parts = split_string_with_limit(text, limit, encoder)
  assert parts == expected_parts, "The function did not split the string as expected."

def test_create_uri():
  name = "Test Name! 123"
  expected_uri = quote(name.lower())
  uri = create_uri(name)
  assert uri == expected_uri, "The URI was not created correctly."

def test_dbscan_cluster():
  X = np.array([[1, 2], [2, 2], [2, 3],
                [8, 7], [8, 8], [7, 7],
                [25, 80], [30, 90], [30, 85]])
  X = np.vstack(X)
  labels = dbscan_cluster(X)
  assert len(set(labels)) > 1, "DBSCAN should find at least 2 clusters."
  assert -1 in labels, "DBSCAN should identify outliers with label -1."

