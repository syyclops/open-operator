from ..vector_store import VectorStore
from azure.storage.blob import ContainerClient

class Files():
    """
    This class is focused on managing files in the blob storage.
    """
    def __init__(self, container_client: ContainerClient, vector_store: VectorStore) -> None:
        self.vector_store = vector_store
        self.container_client = container_client  

    def upload_file(self, file_path: str, portfolio_id: str, building_id: str, extract_meta: bool = True) -> None:
        """
        Upload a file to the blob storage and extract metadata.
        """
        with open(file_path, "rb") as file:
            file_content = file.read()
            file_name = file.name.split("/")[-1]

            # Upload blob
            blob_client = self.container_client.upload_blob(name=f"{portfolio_id}/{building_id}/{file_name}", data=file_content, overwrite=True)
            file_url = blob_client.url

            if extract_meta:
                self.vector_store.extract_and_upload(file_content, file_path, file_url, portfolio_id, building_id)

    
    def list_files(self, portfolio_id: str, building_id: str = None) -> list:
        """
        List all files in a portfolio or building.
        """
        path = f"{portfolio_id}"
        if building_id is not None:
            path += f"/{building_id}"
        blobs = self.container_client.list_blob_names(name_starts_with=path)
        return [blob for blob in blobs]

