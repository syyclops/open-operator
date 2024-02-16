from openoperator import OpenOperator
from openoperator.services import AzureBlobStore, UnstructuredDocumentLoader, PGVectorStore, KnowledgeGraph, OpenAIEmbeddings, Openai, Postgres, Timescale

from dotenv import load_dotenv
load_dotenv()

# Create the different modules that are needed for the operator
blob_store = AzureBlobStore()
document_loader = UnstructuredDocumentLoader()
embeddings = OpenAIEmbeddings()
postgres = Postgres()
vector_store = PGVectorStore(postgres=postgres, embeddings=embeddings)
timescale = Timescale(postgres=postgres)
knowledge_graph = KnowledgeGraph()
ai = Openai(model_name="gpt-4-0125-preview")

operator = OpenOperator(
  blob_store=blob_store,
  document_loader=document_loader,
  vector_store=vector_store,
  timescale=timescale,
  embeddings=embeddings,
  knowledge_graph=knowledge_graph,
  ai=ai,
  base_uri="https://syyclops.com/"
)

operator.server()