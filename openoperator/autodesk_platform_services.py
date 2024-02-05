import os
from base64 import b64encode
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json
from urllib.error import HTTPError

class AutodeskPlatformServices:
    """
    This class handles everything related to the Autodesk platform services.

    - Upload and manage files
    - Extract metadata from files
    - Convert files to different formats
    """
    def __init__(self, client_id: str | None = None, client_secret: str | None = None, bucket_key: str | None = None) -> None:
        self.client_id = client_id or os.environ["FORGE_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["FORGE_CLIENT_SECRET"]
        self.bucket_key = bucket_key or os.environ["FORGE_BUCKET_KEY"]

        # Check if the bucket exists, if it doesn't, create it
        self.token, _ = self.authenticate()

        request = Request(
            f"https://developer.api.autodesk.com/oss/v2/buckets/{self.bucket_key}/details",
            method="GET",
            headers={
                "Authorization": f"Bearer {self.token}",
            }
        )
        try:
            response = urlopen(request)
            response_status = response.status
            if response_status == 404:
                self.create_bucket()
        except HTTPError as error:
            raise Exception(f"Error checking if bucket exists: {error}")


    def create_bucket(self):
        request = Request(
            "https://developer.api.autodesk.com/oss/v2/buckets",
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "x-ads-region": "US"
            },
            data=json.dumps({
                "bucketKey": self.bucket_key,
                "policyKey": "persistent",
            }).encode() 
        )
        try:
            with urlopen(request) as response:
                response_data = response.read()
                response_json = json.loads(response_data)
                return response_json
        except HTTPError as error:
            raise Exception(f"Error creating bucket: {error}")


    def authenticate(self) -> None:
        encoded_auth_string = b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        data={
                "grant_type": "client_credentials",
                "scope": "data:read data:write bucket:create bucket:read bucket:update bucket:delete"
        }
        encoded_data = urlencode(data).encode('utf-8')

        request = Request(
            "https://developer.api.autodesk.com/authentication/v2/token",
            method="POST",
            headers={
                "Authorization": f"Basic {encoded_auth_string}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            },
            data=encoded_data
        )
        
        with urlopen(request) as response:
            response_data = response.read()
            response_json = json.loads(response_data)
            token = response_json["access_token"]
            expires_in = response_json["expires_in"]

            return token, expires_in
        
