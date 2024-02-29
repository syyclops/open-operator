from neo4j.exceptions import Neo4jError
import os
import jwt
from typing import Generator, List
from openoperator.services import BlobStore, Embeddings, DocumentLoader, VectorStore, KnowledgeGraph, LLM, Timescale 
from openoperator.core import Portfolio, Facility, User
from openoperator.utils import create_uri
from openoperator.types import LLMChatResponse, PortfolioModel
from .tool import Tool, ToolParametersSchema

class OpenOperator: 
  """
  This class (one instance is called 'operator') is the center of this project.

  Its responsibilities are:
  - Manage the different modules that are needed for the operator
  - Define the tools that the assistant can use
  - Create and manage portfolios
  - Chat with the assistant
  """
  def __init__(
    self, 
    blob_store: BlobStore,
    embeddings: Embeddings,
    document_loader: DocumentLoader,
    vector_store: VectorStore,
    timescale: Timescale,
    knowledge_graph: KnowledgeGraph,
    llm: LLM,
    base_uri: str = "https://openoperator.com/",
    api_token_secret: str | None = None # Used for JWT on the server
  ) -> None:
    self.blob_store = blob_store
    self.embeddings = embeddings
    self.document_loader = document_loader  
    self.vector_store = vector_store
    self.timescale = timescale
    self.knowledge_graph = knowledge_graph  
    self.llm = llm

    if api_token_secret is None: api_token_secret = os.getenv("API_TOKEN_SECRET")
    self.secret_key = api_token_secret

    self.base_uri = base_uri        

  def user(self, email: str, password: str, full_name: str) -> User:
    return User(self, email, password, full_name)

  def portfolio(self, user: User, portfolio_uri: str) -> Portfolio:
    return Portfolio(self, knowledge_graph=self.knowledge_graph, uri=portfolio_uri, user=user)

  def portfolios(self, user: User) -> list[PortfolioModel]:
    try:
      with self.knowledge_graph.create_session() as session:
        result = session.run("MATCH (u:User {email: $email})-[:HAS_ACCESS_TO]->(c:Customer) return c as Customer", email=user.email)
        data: List[PortfolioModel] = []
        for record in result.data():
          customer = record['Customer']
          data.append(PortfolioModel(name=customer['name'], uri=customer['uri']))
        return data
    except Neo4jError as e:
      raise e
         
  def create_portfolio(self, user: User, name: str) -> Portfolio:
    portfolio_uri = f"{self.base_uri}{create_uri(name)}"
    with self.knowledge_graph.create_session() as session:
      try: 
        result = session.run("""MATCH (u:User {email: $email})
                              CREATE (n:Customer:Resource {name: $name, uri: $uri}) 
                              CREATE (u)-[:HAS_ACCESS_TO]->(n)
                              RETURN n""", name=name, id=str(id), uri=portfolio_uri, email=user.email)
        if result.single() is None:
          raise ValueError("Error creating portfolio")
      except Neo4jError as e:
        raise e
          
    return Portfolio(self, knowledge_graph=self.knowledge_graph, uri=portfolio_uri, user=user)

  def chat(self, messages, portfolio: Portfolio, facility: Facility | None = None, document_uri: str | None = None, verbose: bool = False) -> Generator[LLMChatResponse, None, None]:
    """Interact with the assistant."""
    def search_documents(params: dict):
      """
      A unified document search function that abstracts away the specifics of facility and portfolio.
      """
      if document_uri:
        params["document_uri"] = document_uri
      return facility.documents.search(params) if facility else portfolio.search_documents(params)

    document_search_parameters: ToolParametersSchema = {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The search query to use. Craft your query concisely, focusing on the essence of what you need to find."
        },
      },
      "required": ["query"],
    }
    
    document_search_tool = Tool(
      name="search_documents",
      description="Search documents for metadata. These documents are drawings/plans, O&M manuals, etc.",
      function=search_documents,
      parameters_schema=document_search_parameters
    )

    tools = [document_search_tool]
    for response in self.llm.chat(messages, tools, verbose):
      yield response

  def get_user_from_access_token(self, token):
    """This is used to get a user from a bearer token. It is used in the server."""
    secret_key = self.secret_key
    decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
    email = decoded_token["email"]

    with self.knowledge_graph.create_session() as session:
      result = session.run("MATCH (u:User {email: $email}) RETURN u", email=email)
      user = result.single()
      if user is None:
        raise ValueError("Invalid token")
      user_data = user['u']

    return User(email=user_data['email'], full_name=user_data['fullName'], password=user_data['password'], operator=self)