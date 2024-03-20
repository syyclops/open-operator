from openoperator.domain.repository import DocumentRepository
from openoperator.infrastructure import LLM, VectorStore
from openoperator.domain.model import Tool, ToolParametersSchema, DocumentQuery
from openoperator.domain.model.chat_session import Message, LLMChatResponse
from typing import List, Generator

class AIAssistantService:
  def __init__(self, llm: LLM, document_repository: DocumentRepository, vector_store: VectorStore):
    self.llm = llm
    self.document_repository = document_repository
    self.vector_store = vector_store
  
  def chat(self, portfolio_uri: str, messages: List[Message], facility_uri: str | None = None, document_uri: str | None = None, verbose: bool = False) -> Generator[LLMChatResponse, None, None]:
    # def search_documents(params: dict):
    #   query = params["query"]
    #   document_query = DocumentQuery(query=query, portfolio_uri=portfolio_uri, facility_uri=facility_uri, document_uri=document_uri)
    #   return self.document_repository.search(document_query)
    
    # document_search_parameters: ToolParametersSchema = {
    #   "type": "object",
    #   "properties": {
    #     "query": {
    #       "type": "string",
    #       "description": "The search query to use. Craft your query concisely, focusing on the essence of what you need to find."
    #     },
    #   },
    #   "required": ["query"],
    # }
    
    # document_search_tool = Tool(
    #   name="search_documents",
    #   description="Search documents for metadata. These documents are drawings/plans, O&M manuals, etc.",
    #   function=search_documents,
    #   parameters_schema=document_search_parameters
    # )

    # Get all the documents contents and provide as context to the LLM
    filter = {
      "portfolio_uri": portfolio_uri,
    }
    if facility_uri:
      filter["facility_uri"] = facility_uri
    if document_uri:
      filter["document_uri"] = document_uri
    documents = self.vector_store.list_documents(filter=filter)

    context = "Here is all the information about the portfolio or facility the user is interested in. Use it to help answer their questions\n\n"
    for document in documents:
      content = document.content.replace("\n", " ")
      context += f"Facility: {document.metadata['facility_uri']}\n{content}\n\n"

    print(context)

    messages.insert(0, Message(role="system", content=context))

    tools = []
    return self.llm.chat(messages, tools, verbose)
