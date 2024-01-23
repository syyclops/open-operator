from ..database import vector_store
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError

class ETL():
    def __init__(self, api_key: str, api_url: str) -> None:
        self.unstructured_client = UnstructuredClient(api_key_auth=api_key, server_url=api_url)

    def load_file(self, file_path: str):
        with open(file_path, "rb") as f:
            # Note that this currently only supports a single file
            files=shared.Files(
                content=f.read(),
                file_name=file_path,
            )

        req = shared.PartitionParameters(
            files=files,
            strategy='auto',
            pdf_infer_table_structure=True,
            skip_infer_table_types=[],
            languages=["eng"],
        )

        try:
            resp = self.unstructured_client.general.partition(req)
            elements = resp.elements
            print(elements[0])

        except SDKError as e:
            print(e)