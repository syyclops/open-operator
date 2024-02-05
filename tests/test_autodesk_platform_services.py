from unittest.mock import MagicMock, patch
import os
import json
from openoperator.autodesk_platform_services import AutodeskPlatformServices

@patch('openoperator.autodesk_platform_services.urlopen')
def test_init(mock_urlopen):
    # Setup environment variables
    os.environ['FORGE_CLIENT_ID'] = 'client_id'
    os.environ['FORGE_CLIENT_SECRET'] = 'client_secret'
    os.environ['FORGE_BUCKET_KEY'] = 'bucket_key'

    # Create a mock response that contains a JSON string
    mock_response_data = json.dumps({
        'access_token': 'token',
        'expires_in': 3600
    }).encode('utf-8')  # Encode to bytes, as it would be in a real HTTP response

    # Create a mock urlopen instance
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = mock_response_data  # Mock the read() method
    mock_response.__enter__.return_value = mock_response  # If context manager is used
    mock_urlopen.return_value = mock_response

    # Correctly set up side_effect for all three expected calls
    mock_response_bucket_check_fail = MagicMock()
    mock_response_bucket_check_fail.status = 404
    mock_response_bucket_check_fail.read.return_value = b'{}'
    mock_response_bucket_check_fail.__enter__.return_value = mock_response_bucket_check_fail

    mock_response_create_bucket_success = MagicMock()
    mock_response_create_bucket_success.status = 200
    mock_response_create_bucket_success.read.return_value = b'{}'  # Adjust as needed for bucket creation response
    mock_response_create_bucket_success.__enter__.return_value = mock_response_create_bucket_success

    # Ensure side_effect simulates all three operations in sequence
    mock_urlopen.side_effect = [mock_response, mock_response_bucket_check_fail, mock_response_create_bucket_success]

    # Initialize AutodeskPlatformServices, this should use the mocked urlopen
    service = AutodeskPlatformServices()

    # Verify urlopen was called correctly, called once to authenticate and once to check if the bucket exists
    assert mock_urlopen.call_count == 3
    assert mock_urlopen.call_args_list[0][0][0].full_url == "https://developer.api.autodesk.com/authentication/v2/token"
    assert mock_urlopen.call_args_list[1][0][0].full_url == "https://developer.api.autodesk.com/oss/v2/buckets/bucket_key/details"
    assert mock_urlopen.call_args_list[2][0][0].full_url == "https://developer.api.autodesk.com/oss/v2/buckets"




