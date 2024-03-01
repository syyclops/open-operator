from .blob_store import BlobStore
import os
from azure.storage.blob import ContainerClient, ContentSettings
import urllib

class AzureBlobStore(BlobStore):
  def __init__(self, container_client_connection_string: str | None = None, container_name: str | None = None) -> None:
    # Create the container client
    if container_client_connection_string is None:
      container_client_connection_string = os.environ['AZURE_STORAGE_CONNECTION_STRING']
    if container_name is None:
      container_name = os.environ['AZURE_CONTAINER_NAME']
    self.container_client = ContainerClient.from_connection_string(container_client_connection_string, container_name=container_name)

    # Check if the container exists, if it doesn't, create it
    if not self.container_client.exists():
      self.container_client.create_container(public_access="blob")

  def upload_file(self, file_content: bytes, file_name: str, file_type: str) -> str:
    content_settings = ContentSettings(content_type=file_type)
    blob_client = self.container_client.upload_blob(name=file_name, data=file_content, overwrite=True, content_settings=content_settings)
    return blob_client.url

  def download_file(self, url: str) -> bytes:
    clean_url = urllib.parse.unquote(url)
    name = clean_url.split('/')[-1]
    blob = self.container_client.get_blob_client(name)
    return blob.download_blob().readall()
    
  def list_files(self, path: str) -> list:
    blobs = self.container_client.list_blob_names(name_starts_with=path)
    return [blob for blob in blobs]
  
  def delete_file(self, url: str) -> None:
    clean_url = urllib.parse.unquote(url)
    name = clean_url.split('/')[-1]
    blob = self.container_client.get_blob_client(name)
    blob.delete_blob()