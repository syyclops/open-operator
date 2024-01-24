from ...vector_store import vector_store
from langchain_community.document_loaders import UnstructuredAPIFileLoader


class Files():
    def __init__(self, assistant) -> None:
        self.assistant = assistant

    def upload_file(self, file_path: str) -> None:
        loader = UnstructuredAPIFileLoader(
            file_path=file_path,
            api_key="FAKE_API_KEY",
        )

        docs = loader.load()

        vector_store.add_documents(docs)

    def similarity_search(self, query: str, k: int) -> list:
        return vector_store.similarity_search(query, k)

        
