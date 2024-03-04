from openoperator.domain.repository import DocumentRepository
from openoperator.infrastructure import LLM
from openoperator.domain.model import Tool, ToolParametersSchema, DocumentQuery
from openoperator.domain.model.chat_session import Message, LLMChatResponse
from typing import List, Generator

class AIAssistantService:
  def __init__(self, llm: LLM, document_repository: DocumentRepository):
    self.llm = llm
    self.document_repository = document_repository
  
  def chat(self, portfolio_uri: str, messages: List[Message], facility_uri: str | None = None, document_uri: str | None = None, verbose: bool = False) -> Generator[LLMChatResponse, None, None]:
    def search_documents(params: dict):
      query = params["query"]
      document_query = DocumentQuery(query=query, portfolio_uri=portfolio_uri, facility_uri=facility_uri, document_uri=document_uri)
      return self.document_repository.search(document_query)
    
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

    messages = [message.model_dump() for message in messages]
    return self.llm.chat(messages, tools, verbose)
