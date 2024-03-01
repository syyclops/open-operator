from abc import ABC, abstractmethod

class BlobStore(ABC):
  @abstractmethod
  def upload_file(self, file_content: bytes, file_name: str, file_type: str) -> str:
    """
    Upload a file to the blob storage.
    """

  @abstractmethod
  def download_file(self, url: str) -> bytes:
    """
    Download a file from the blob storage.
    """

  def delete_file(self, url: str) -> None:
    """
    Delete a file from the blob storage.
    """

  @abstractmethod
  def list_files(self, path: str) -> list:
    """
    List all files in a path.
    """