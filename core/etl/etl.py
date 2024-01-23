from ..database.vector_store import VectorStore
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError
import os

class ETL():
    def __init__(self) -> None:
        self.unstructured_client = UnstructuredClient(api_key_auth=os.environ.get("UNSTRUCTURED_API_KEY"), server_url=os.environ.get("UNSTRUCTURED_URL"))

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
            print(resp)
        except SDKError as e:
            print(e)