from ...services.blob_store import BlobStore
from ...services.vector_store import VectorStore

class Files():
    """
    This class is focused on managing files in the blob storage.
    """
    def __init__(self, blob_store: BlobStore, vector_store: VectorStore) -> None:
        self.vector_store = vector_store
        self.blob_store = blob_store

    def upload_file(self, file_path: str, portfolio_id: str, building_id: str, extract_meta: bool = True) -> None:
        """
        Upload a file to the blob storage and extract metadata.
        """
        self.blob_store.upload_file(file_path=file_path)

    
    def list_files(self, portfolio_id: str, building_id: str = None) -> list:
        """
        List all files in a portfolio or building.
        """
        path = f"{portfolio_id}"
        if building_id is not None:
            path += f"/{building_id}"
        return self.blob_store.list_files(path=path)

