from ...services.blob_store import BlobStore
from ...services.vector_store import VectorStore
from ...services.document_loader import DocumentLoader

class Files():
    """
    This class is focused on managing files for the assistant.

    Its responsibilities are:

    - Manage the files in the blob storage
    - Extract metadata from files and upload to vector store
    """
    def __init__(self, blob_store: BlobStore, vector_store: VectorStore, document_loader: DocumentLoader) -> None:
        self.vector_store = vector_store
        self.blob_store = blob_store
        self.document_loader = document_loader

    def upload_file(self, file_content: bytes, file_name: str, portfolio_id: str, building_id: str) -> None:
        """
        Upload a file to the blob storage and vector store
        """
        path = f"{portfolio_id}/{building_id}/{file_name}"
        self.blob_store.upload_file(file_content=file_content, file_name=path)
        docs = self.document_loader.load(file_content=file_content, file_path=file_name)

        # Add metadata to vector store
        for doc in docs:
            doc.metadata['portfolio_id'] = portfolio_id
            doc.metadata['building_id'] = building_id

        self.vector_store.add_documents(docs)
    
    def search_metadata(self, query: str, limit: int = 5, filter: dict | None = None) -> list:
        """
        Search metadata for a query.
        """
        return self.vector_store.similarity_search(query=query, limit=limit, filter=filter)
    
    def list_files(self, portfolio_id: str, building_id: str = None) -> list:
        """
        List all files in a portfolio or building.
        """
        path = f"{portfolio_id}"
        if building_id is not None:
            path += f"/{building_id}"
        return self.blob_store.list_files(path=path)