from .knowledge_graph import KnowledgeGraph
from .portfolio import Portfolio
from .facility import Facility
from neo4j.exceptions import Neo4jError
from .blob_store.blob_store import BlobStore
from .embeddings.embeddings import Embeddings
from .document_loader.document_loader import DocumentLoader
from .vector_store.vector_store import VectorStore
from .llm.llm import LLM
from .utils import create_uri
from .server import server

class OpenOperator: 
    """
    This class (one instance is called 'operator') is the center of this project.

    Its responsibilities are:

    - Manage the different modules that are needed for the operator
    - Define the tools that the assistant can use
    - Create and manage portfolios
    - Chat with the assistant
    - Start the server
    """
    def __init__(
        self, 
        blob_store: BlobStore,
        embeddings: Embeddings,
        document_loader: DocumentLoader,
        vector_store: VectorStore,
        knowledge_graph: KnowledgeGraph,
        llm: LLM,
    ) -> None:
        self.blob_store = blob_store
        self.embeddings = embeddings
        self.document_loader = document_loader  
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph  
        self.neo4j_driver = knowledge_graph.neo4j_driver
        self.llm = llm
    
        # Define the tools that the assistant can use
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_building_documents",
                    "description": "Search building documents for metadata. These documents are drawings/plans, O&M manuals, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to use.",
                            },
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

        self.base_uri = "https://openoperator.com/"

    def portfolio(self, portfolio_uri: str) -> Portfolio:
        return Portfolio(self, neo4j_driver=self.neo4j_driver, uri=portfolio_uri)

    def portfolios(self) -> list:
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Portfolio) RETURN n")
            return [record['n'] for record in result.data()]
        
    def create_portfolio(self, name: str) -> Portfolio:
        portfolio_uri = f"{self.base_uri}{create_uri(name)}"
        with self.neo4j_driver.session() as session:
            try: 
                result = session.run("CREATE (n:Portfolio:Resource {name: $name, uri: $uri}) RETURN n", name=name, id=str(id), uri=portfolio_uri)
                if result.single() is None:
                    raise Exception("Error creating portfolio")
            except Neo4jError as e:
                raise Exception(f"Error creating portfolio: {e.message}")
            
        return Portfolio(self, neo4j_driver=self.neo4j_driver, uri=portfolio_uri)

    def chat(self, messages, portfolio: Portfolio, facility: Facility | None = None, verbose: bool = False):
        """
        Interact with the assistant.
        """
        available_functions = {
            "search_building_documents": facility.search_documents if facility else portfolio.search_documents,
        }

        for response in self.llm.chat(messages, self.tools, available_functions, verbose):
            yield response

    def server(self, *args, **kwargs):
        server(self, *args, **kwargs)