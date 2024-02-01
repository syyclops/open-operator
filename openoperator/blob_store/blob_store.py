from abc import ABC, abstractmethod

class BlobStore(ABC):
    @abstractmethod
    def upload_file(self, file_content: bytes, file_name: str, file_type: str) -> str:
        """
        Upload a file to the blob storage.
        """
        pass

    @abstractmethod
    def list_files(self, path: str) -> list:
        """
        List all files in a path.
        """
        pass


