import unittest
from unittest.mock import patch, MagicMock
import os
import json
from openoperator.autodesk_platform_services import AutodeskPlatformServices
from base64 import b64encode
from urllib.parse import urlencode

class TestAutodeskPlatformServices(unittest.TestCase):
    @patch('openoperator.autodesk_platform_services.urlopen')
    def setUp(self, mock_urlopen):
        # Setup environment variables for testing
        os.environ['FORGE_CLIENT_ID'] = 'client_id'
        os.environ['FORGE_CLIENT_SECRET'] = 'client_secret'
        os.environ['FORGE_BUCKET_KEY'] = 'bucket_key'

        # Mock authentication response
        mock_auth_response = MagicMock()
        mock_auth_response.read.return_value = json.dumps({
            'access_token': 'token',
            'expires_in': 3600
        }).encode('utf-8')
        mock_auth_response.__enter__.return_value = mock_auth_response

        # Mock bucket check failure (bucket does not exist)
        mock_bucket_check_fail = MagicMock()
        mock_bucket_check_fail.status = 404
        mock_bucket_check_fail.read.return_value = b'{}'
        mock_bucket_check_fail.__enter__.return_value = mock_bucket_check_fail

        # Mock bucket creation success
        mock_bucket_create_success = MagicMock()
        mock_bucket_create_success.status = 200
        mock_bucket_create_success.read.return_value = b'{}'
        mock_bucket_create_success.__enter__.return_value = mock_bucket_create_success

        # Setup side_effect to simulate sequential calls to urlopen
        mock_urlopen.side_effect = [mock_auth_response, mock_bucket_check_fail, mock_bucket_create_success]

        # Instance to be used in tests
        self.service = AutodeskPlatformServices()

        self.assertEqual(mock_urlopen.call_count, 3)

    def test_init(self):
        # Check if the AutodeskPlatformServices instance was created successfully
        self.assertIsInstance(self.service, AutodeskPlatformServices)

        # Check that authentication and bucket check/create were attempted
        self.assertEqual(self.service.token, 'token')

    @patch('openoperator.autodesk_platform_services.urlopen')
    def test_authenticate(self, mock_urlopen):
        # Mock authentication response
        mock_auth_response = MagicMock()
        mock_auth_response.read.return_value = json.dumps({
            'access_token': 'token',
            'expires_in': 3600
        }).encode('utf-8')
        mock_auth_response.__enter__.return_value = mock_auth_response

        # Mock urlopen to return the mock_auth_response
        mock_urlopen.return_value = mock_auth_response

        # Call authenticate
        token, _ = self.service.authenticate()

        # Check that the token was returned
        self.assertEqual(token, 'token')


        
        


if __name__ == '__main__':
    unittest.main()
