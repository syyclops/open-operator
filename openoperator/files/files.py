from ..vector_store import VectorStore
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError

class Files():
    def __init__(self, vector_store: VectorStore, unstructured_client: UnstructuredClient) -> None:
        self.vector_store = vector_store
        self.unstructured_client = unstructured_client

    def upload_file(self, file_path: str) -> None:
        file = open(file_path, "rb")

        req = shared.PartitionParameters(
            # Note that this currently only supports a single file
            files=shared.Files(
                content=file.read(),
                file_name=file_path,
            ),
            # Other partition params
            strategy="fast",
            pdf_infer_table_structure=True,
            skip_infer_table_types=[],
            chunking_strategy="by_title",
            multipage_sections=True,
        )

        try:
            res = self.unstructured_client.general.partition(req)
            for element in res.elements:
                print(element)
                print()
        except SDKError as e:
            print(e)

    def similarity_search(self, query: str, k: int) -> list:
        return self.vector_store.similarity_search(query, k)