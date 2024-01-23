from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from dotenv import load_dotenv
import os

load_dotenv()

embeddings = OpenAIEmbeddings()

vector_store = PGVector(
    collection_name=os.environ.get("POSTGRES_EMBEDDINGS_TABLE"),
    connection_string=os.environ.get("POSTGRES_CONN"),
    embedding_function=embeddings,
)

