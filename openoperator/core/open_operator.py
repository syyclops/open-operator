from typing import Generator 
from openoperator.types import LLMChatResponse
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
    llm: LLM,
    base_uri: str = "https://openoperator.com/",
    # api_token_secret: str | None = None # Used for JWT on the server
  ) -> None:
    self.blob_store = blob_store
    self.embeddings = embeddings
    self.document_loader = document_loader  
    self.vector_store = vector_store
    self.timescale = timescale
    self.llm = llm

    self.base_uri = base_uri 

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