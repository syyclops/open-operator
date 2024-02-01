from unittest.mock import MagicMock, patch
from openoperator.blob_store import AzureBlobStore
from azure.storage.blob import ContentSettings

@patch('azure.storage.blob.ContainerClient.from_connection_string')
def test_upload_file(mock_from_connection_string):
    # Arrange
    mock_container_client = MagicMock()
    mock_from_connection_string.return_value = mock_container_client
    mock_container_client.exists.return_value = True
    mock_blob_client = MagicMock()
    mock_blob_client.url = 'http://test_url'
    mock_container_client.upload_blob.return_value = mock_blob_client
    azure_blob_store = AzureBlobStore('test_connection_string', 'test_container_name')

    # Act
    result = azure_blob_store.upload_file(b'test_content', 'test_file', 'test_type')

    # Assert
    mock_from_connection_string.assert_called_once_with('test_connection_string', container_name='test_container_name')
    mock_container_client.upload_blob.assert_called_once_with(name='test_file', data=b'test_content', overwrite=True, content_settings=ContentSettings(content_type='test_type'))
    assert result == 'http://test_url'

@patch('azure.storage.blob.ContainerClient.from_connection_string')
def test_list_files(mock_from_connection_string):
    # Arrange
    mock_container_client = MagicMock()
    mock_from_connection_string.return_value = mock_container_client
    mock_container_client.exists.return_value = True
    mock_container_client.list_blob_names.return_value = ['file1', 'file2']
    azure_blob_store = AzureBlobStore('test_connection_string', 'test_container_name')

    # Act
    result = azure_blob_store.list_files('test_path')

    # Assert
    mock_from_connection_string.assert_called_once_with('test_connection_string', container_name='test_container_name')
    mock_container_client.list_blob_names.assert_called_once_with(name_starts_with='test_path')
    assert result == ['file1', 'file2']

@patch('azure.storage.blob.ContainerClient.from_connection_string')
def test_container_does_not_exist(mock_from_connection_string):
    # Arrange
    mock_container_client = MagicMock()
    mock_from_connection_string.return_value = mock_container_client
    mock_container_client.exists.return_value = False
    azure_blob_store = AzureBlobStore('test_connection_string', 'test_container_name')

    # Act and Assert
    mock_container_client.create_container.assert_called_once_with(public_access="blob")