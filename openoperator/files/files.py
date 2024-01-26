from ..vector_store import VectorStore
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError
from azure.storage.blob import ContainerClient

class Files():
    def __init__(self, container_client: ContainerClient, vector_store: VectorStore, unstructured_client: UnstructuredClient) -> None:
        self.vector_store = vector_store
        self.unstructured_client = unstructured_client
        self.container_client = container_client  

    def upload_file(self, file_path: str, portfolio_id: str, building_id: str, extract_meta: bool = True) -> None:
        """
        Upload a file to the blob storage and extract metadata.
        """
        # Read the file
        file = open(file_path, "rb")
        file_content = file.read()
        file_name = file.name.split("/")[-1]

        # Upload blob
        self.container_client.upload_blob(name=f"{portfolio_id}/{building_id}/{file_name}", data=file_content, overwrite=True)

        if extract_meta:
            try:
                # Extract metadata
                req = shared.PartitionParameters(
                    # Note that this currently only supports a single file
                    files=shared.Files(
                        content=file_content,
                        file_name=file_path,
                    ),
                    # Other partition params
                    strategy="fast",
                    pdf_infer_table_structure=True,
                    skip_infer_table_types=[],
                    chunking_strategy="by_title",
                    multipage_sections=True,
                )

                res = self.unstructured_client.general.partition(req)

                # Upload to vector store
                self.vector_store.add_documents(res.elements)
            except SDKError as e:
                print(e)

    def similarity_search(self, query: str, k: int) -> list:
        return self.vector_store.similarity_search(query, k)