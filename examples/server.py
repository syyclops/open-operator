from openoperator import OpenOperator
from openoperator.blob_store import AzureBlobStore
from openoperator.document_loader import UnstructuredDocumentLoader
from openoperator.vector_store import PGVectorStore
from openoperator.embeddings import OpenAIEmbeddings
from openoperator.knowledge_graph import KnowledgeGraph
from openoperator.llm import OpenAILLM

from dotenv import load_dotenv
load_dotenv()

# Create the different modules that are needed for the operator
blob_store = AzureBlobStore()
document_loader = UnstructuredDocumentLoader()
embeddings = OpenAIEmbeddings()
vector_store = PGVectorStore(embeddings=embeddings)
knowledge_graph = KnowledgeGraph()
llm = OpenAILLM(model_name="gpt-4-0125-preview")

operator = OpenOperator(
    blob_store=blob_store,
    document_loader=document_loader,
    vector_store=vector_store,
    embeddings=embeddings,
    knowledge_graph=knowledge_graph,
    llm=llm
)

operator.server()

