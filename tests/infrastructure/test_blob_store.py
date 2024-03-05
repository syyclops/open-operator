from unittest.mock import patch, MagicMock
from openoperator.infrastructure.blob_store import AzureBlobStore
import os
from azure.storage.blob import ContentSettings

@patch('openoperator.infrastructure.blob_store.azure_blob_store.ContainerClient')
def test_upload_file(mock_container_client_class):
  # Setup environment variables
  os.environ['AZURE_STORAGE_CONNECTION_STRING'] = 'connection_string'
  os.environ['AZURE_CONTAINER_NAME'] = 'container_name'

  # Create a mock container client instance
  mock_container_client = MagicMock()
  mock_container_client.exists.return_value = True  # Assume the container exists
  mock_container_client_class.from_connection_string.return_value = mock_container_client

  # Initialize AzureBlobStore, this should use the mocked ContainerClient
  store = AzureBlobStore()

  # Verify ContainerClient.from_connection_string was called correctly
  mock_container_client_class.from_connection_string.assert_called_once_with('connection_string', container_name='container_name')

  # Perform the upload
  file_content = b'file_content'
  file_name = 'file_name'
  file_type = 'file_type'
  content_settings = ContentSettings(content_type=file_type)
  store.upload_file(file_content, file_name, file_type)
  
  # Check if upload_blob was called with the correct arguments
  mock_container_client.upload_blob.assert_called_once_with(name=file_name, data=file_content, overwrite=True, content_settings=content_settings)

@patch('openoperator.infrastructure.blob_store.azure_blob_store.ContainerClient')
def test_delete_file(mock_container_client_class):
  # Setup environment variables
  os.environ['AZURE_STORAGE_CONNECTION_STRING'] = 'connection_string'
  os.environ['AZURE_CONTAINER_NAME'] = 'container_name'

  # Create a mock container client instance
  mock_container_client = MagicMock()
  mock_container_client.exists.return_value = True

  # Assume the container exists
  mock_container_client_class.from_connection_string.return_value = mock_container_client

  # Initialize AzureBlobStore, this should use the mocked ContainerClient
  store = AzureBlobStore()

  # Perform the delete
  url = 'url'
  store.delete_file(url)

  # Check if get_blob_client was called with the correct arguments
  mock_container_client.get_blob_client.assert_called_once_with('url')

  # Check if delete_blob was called
  mock_container_client.get_blob_client.return_value.delete_blob.assert_called_once()

@patch('openoperator.infrastructure.blob_store.azure_blob_store.ContainerClient')
def test_list_files(mock_container_client_class):
  # Setup environment variables
  os.environ['AZURE_STORAGE_CONNECTION_STRING'] = 'connection_string'
  os.environ['AZURE_CONTAINER_NAME'] = 'container_name'

  # Create a mock container client instance
  mock_container_client = MagicMock()
  mock_container_client.exists.return_value = True

  # Assume the container exists
  mock_container_client_class.from_connection_string.return_value = mock_container_client

  # Initialize AzureBlobStore, this should use the mocked ContainerClient
  store = AzureBlobStore()

  # Perform the list
  path = 'path'
  store.list_files(path)

  # Check if list_blob_names was called with the correct arguments
  mock_container_client.list_blob_names.assert_called_once_with(name_starts_with=path)