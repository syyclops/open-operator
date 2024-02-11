from openoperator import OpenOperator
from openoperator.services.blob_store import AzureBlobStore
from openoperator.services.document_loader import UnstructuredDocumentLoader
from openoperator.services.vector_store import PGVectorStore
from openoperator.services.embeddings import OpenAIEmbeddings
from openoperator.services.knowledge_graph import KnowledgeGraph
from openoperator.services.ai import Openai

from dotenv import load_dotenv
load_dotenv()

# Create the different modules that are needed for the operator
blob_store = AzureBlobStore()
document_loader = UnstructuredDocumentLoader()
embeddings = OpenAIEmbeddings()
vector_store = PGVectorStore(embeddings=embeddings)
knowledge_graph = KnowledgeGraph()
ai = Openai(model_name="gpt-4-0125-preview")

operator = OpenOperator(
    blob_store=blob_store,
    document_loader=document_loader,
    vector_store=vector_store,
    embeddings=embeddings,
    knowledge_graph=knowledge_graph,
    ai=ai,
    base_uri="https://syyclops.com/"
)

operator.server()