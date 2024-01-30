from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError
import os

class Document:
    def __init__(self, text: str, metadata):
        self.text = text
        self.metadata = metadata

class DocumentLoader():
    def __init__(
            self,
            unstructured_api_key: str | None = None,
            unstructured_api_url: str | None = None,
    ) -> None:
        if unstructured_api_key is None:
            unstructured_api_key = os.environ['UNSTRUCTURED_API_KEY']
        if unstructured_api_url is None:
            unstructured_api_url = os.environ['UNSTRUCTURED_URL']
        s = UnstructuredClient(api_key_auth=unstructured_api_key, server_url=unstructured_api_url)

        self.unstructured_client = s
    
    def load(self, file_content: bytes, file_path: str) -> list[Document]:
        """
        Use unstructured client to extract metadata from a file and upload to vector store.
        """
        try:
            # Extract metadata
            req = shared.PartitionParameters(
                # Note that this currently only supports a single file
                files=shared.Files(
                    content=file_content,
                    file_name=file_path,
                ),
                # Other partition params
                strategy="auto",
                pdf_infer_table_structure=True,
                skip_infer_table_types=[],
                chunking_strategy="by_title",
                multipage_sections=True,
            )

            res = self.unstructured_client.general.partition(req)

            return [Document(text=element['text'], metadata=element['metadata']) for element in res.elements]
        except SDKError as e:
            print("Error extracting metadata")