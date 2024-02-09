
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared
from unstructured_client.models.errors import SDKError
import os
from typing import List
from .document_loader import DocumentLoader
from openoperator.types import Document

class UnstructuredDocumentLoader(DocumentLoader):
    """
    Using https://unstructured.io/ to extract metadata from a file and upload to vector store.
    """
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
    
    def load(self, file_content: bytes, file_path: str) -> List[Document]:
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
                skip_infer_table_types=[""],
                max_characters=1500,
                new_after_n_chars=1500,
                chunking_strategy="by_title",
                combine_under_n_chars=500,
                coordinates=True
            )

            res = self.unstructured_client.general.partition(req)
            docs = [Document(text=element['text'], metadata=element['metadata']) for element in res.elements]
            docs = [doc for doc in docs if doc.text] # Remove any where text is empty
            return docs
        except SDKError as e:
            print("Error extracting metadata")