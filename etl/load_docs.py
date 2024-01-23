
from etl.connectors import vector_store
from etl.connectors import loader
from langchain_community.document_loaders import UnstructuredAPIFileLoader

def load_document(file_path: str):
    loader = UnstructuredAPIFileLoader(
        file_path=file_path,
        api_key="FAKE_API_KEY",
        url="http://0.0.0.0:8000",
    )

    docs = loader.load()

    # Add metadata to docs
    for doc in docs:
        print(doc)
        doc.metadata.update({"customerUri": "test"})


    vector_store.add_documents(docs)