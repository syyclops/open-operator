from openoperator.infrastructure import AzureBlobStore, UnstructuredDocumentLoader, PGVectorStore, KnowledgeGraph, OpenAIEmbeddings, OpenaiLLM, Postgres 
from openoperator.domain.repository import DocumentRepository
from openoperator.domain.service import AIAssistantService
import argparse
from dotenv import load_dotenv
load_dotenv()

def main():
  # Create the argument parser
  parser = argparse.ArgumentParser()
  parser.add_argument('--portfolio_uri', type=str, help='The portfolio ID to use for the chat', default="https://syyclops.com/example")
  parser.add_argument('--verbose', type=bool, default=False, help='Print verbose output') 
  args = parser.parse_args()
  verbose = args.verbose
  portfolio_uri = args.portfolio_uri

  llm_system_prompt = """You are an an AI Assistant that specializes in building operations and maintenance.
  Your goal is to help facility owners, managers, and operators manage their facilities and buildings more efficiently.
  Make sure to always follow ASHRAE guildelines.
  Don't be too wordy. Don't be too short. Be just right.
  Don't make up information. If you don't know, say you don't know.
  Always respond with markdown formatted text."""

  # Infrastructure
  knowledge_graph = KnowledgeGraph()
  blob_store = AzureBlobStore()
  document_loader = UnstructuredDocumentLoader()
  embeddings = OpenAIEmbeddings()
  postgres = Postgres()
  vector_store = PGVectorStore(postgres=postgres, embeddings=embeddings)
  llm = OpenaiLLM(model_name="gpt-4-0125-preview", system_prompt=llm_system_prompt)

  # Repositories
  document_repository = DocumentRepository(kg=knowledge_graph, blob_store=blob_store, document_loader=document_loader, vector_store=vector_store)

  # Services
  ai_assistant_service = AIAssistantService(llm=llm, document_repository=document_repository)

  messages = []

  while True:
    # Get input from user
    user_input = input("Enter input: ")

    # If the user enters "exit" then exit the program
    if user_input == "exit":
      break

    messages.append({
        "role": "user",
        "content": user_input
    })

    content = ""
    for response in ai_assistant_service.chat(portfolio_uri=portfolio_uri, messages=messages, verbose=verbose):
      if response.type == "tool_selected":
        print(f"Tool selected: {response.tool_name}")
      if response.type == "content":
        content = response.content
        print(content, flush=True, end="")

    messages.append({
        "role": "assistant",
        "content": content
    })

    print()


if __name__ == "__main__":
  main()