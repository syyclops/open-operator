from langchain_community.document_loaders import UnstructuredAPIFileLoader
import os

class Files():
    def __init__(self, vector_store) -> None:
        # self.assistant = assistant
        self.vector_store = vector_store

    def upload_file(self, file_path: str) -> None:
        loader = UnstructuredAPIFileLoader(
            file_path=file_path,
            api_key=os.environ.get("UNSTRUCTURED_API_KEY"),
            url=os.environ.get("UNSTRUCTURED_URL")
        )
        docs = loader.load()

        self.vector_store.add_documents(docs)

    def similarity_search(self, query: str, k: int) -> list:
        return self.vector_store.similarity_search(query, k)