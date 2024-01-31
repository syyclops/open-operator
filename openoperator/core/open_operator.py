from ..services.knowledge_graph import KnowledgeGraph
from ..services.blob_store import BlobStore
from ..services.embeddings import Embeddings
from ..services.document_loader import DocumentLoader
from ..services.vector_store import VectorStore
from ..services.llm import LLM
import uuid
from .portfolio import Portfolio
from urllib.parse import quote
from neo4j.exceptions import Neo4jError

class OpenOperator: 
    """
    This class (one instance is called 'operator') is the center of this project.

    Its responsibilities are:

    - Provide a chat method that can be used to interact with the assistant
    - Provide a files object that can be used to upload files to the assistant
    - Provide a knowledge graph object that can be used to interact with the knowledge graph of the assistant
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
        # Services
        self.blob_store = blob_store
        self.embeddings = embeddings
        self.document_loader = document_loader  
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph  
        self.neo4j_driver = knowledge_graph.neo4j_driver
        self.llm = llm

    def portfolio(self, portfolio_id: str) -> Portfolio:
        return Portfolio(self, neo4j_driver=self.neo4j_driver, portfolio_id=portfolio_id)

    def portfolios(self) -> list:
        """
        Get all portfolios.
        """
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (n:Portfolio) RETURN n")
            return [record['n'] for record in result.data()]
        
    def create_portfolio(self, name: str) -> Portfolio:
        """
        Create a portfolio.
        """
        id = uuid.uuid4()
        portfolio_uri = f"https://openoperator.com/{quote(name)}"
        with self.neo4j_driver.session() as session:
            try: 
                result = session.run("CREATE (n:Portfolio:Resource {name: $name, id: $id, uri: $uri}) RETURN n", name=name, id=str(id), uri=portfolio_uri)
                result.consume()
            except Neo4jError as e:
                raise Exception(f"Error creating portfolio: {e.message}")
        return Portfolio(self, neo4j_driver=self.neo4j_driver, portfolio_id=str(id), uri=portfolio_uri)

    def chat(self, messages, verbose: bool = False):
        self.llm.chat(messages, verbose)