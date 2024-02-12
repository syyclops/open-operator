from neo4j.exceptions import Neo4jError
import os
import jwt
from openoperator.services import BlobStore, Embeddings, DocumentLoader, VectorStore, KnowledgeGraph, AI
from openoperator.core import Portfolio, Facility, User, server
from openoperator.utils import create_uri

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
        ai: AI,
        base_uri: str = "https://openoperator.com/",
        api_token_secret: str | None = None # Used for JWT on the server
    ) -> None:
        self.blob_store = blob_store
        self.embeddings = embeddings
        self.document_loader = document_loader  
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph  
        self.ai = ai

        if api_token_secret is None:
            api_token_secret = os.getenv("API_TOKEN_SECRET")
        self.secret_key = api_token_secret
    
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

        self.base_uri = base_uri        

    def user(self, email: str, password: str, full_name: str) -> User:
        return User(self, email, password, full_name)

    def portfolio(self, user: User, portfolio_uri: str) -> Portfolio:
        return Portfolio(self, knowledge_graph=self.knowledge_graph, uri=portfolio_uri, user=user)

    def portfolios(self, user: User) -> list:
        with self.knowledge_graph.create_session() as session:
            result = session.run("MATCH (u:User {email: $email})-[:HAS_ACCESS_TO]->(c:Customer) return c as Customer", email=user.email)
            data = []
            for record in result.data():
                customer = record['Customer']
                data.append({
                    "name": customer['name'],
                    "uri": customer['uri'],
                })
            return data
         
    def create_portfolio(self, user: User, name: str) -> Portfolio:
        portfolio_uri = f"{self.base_uri}{create_uri(name)}"
        with self.knowledge_graph.create_session() as session:
            try: 
                result = session.run("""
                                     MATCH (u:User {email: $email})
                                     CREATE (n:Customer:Resource {name: $name, uri: $uri}) 
                                     CREATE (u)-[:HAS_ACCESS_TO]->(n)
                                     RETURN n
                                     """, name=name, id=str(id), uri=portfolio_uri, email=user.email)
                if result.single() is None:
                    raise Exception("Error creating portfolio")
            except Neo4jError as e:
                raise Exception(f"Error creating portfolio: {e}")
            
        return Portfolio(self, knowledge_graph=self.knowledge_graph, uri=portfolio_uri, user=user)

    def chat(self, messages, portfolio: Portfolio, facility: Facility | None = None, verbose: bool = False):
        """
        Interact with the assistant.
        """
        available_functions = {
            "search_building_documents": facility.documents.search if facility else portfolio.search_documents,
        }

        for response in self.ai.chat(messages, self.tools, available_functions, verbose):
            yield response

    def transcribe(self, audio) -> str:
        """
        Transcribe audio to text.
        """
        return self.ai.transcribe(audio)

    def get_user_from_access_token(self, token):
        """
        This is used to get a user from a bearer token. It is used in the server.
        """
        secret_key = self.secret_key
        decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
        email = decoded_token["email"]

        with self.knowledge_graph.create_session() as session:
            result = session.run("MATCH (u:User {email: $email}) RETURN u", email=email)
            user = result.single()
            if user is None:
                raise Exception("Invalid token")
            user_data = user['u']

        return User(email=user_data['email'], full_name=user_data['fullName'], password=user_data['password'], operator=self)

    def server(self, *args, **kwargs):
        server(self, *args, **kwargs)