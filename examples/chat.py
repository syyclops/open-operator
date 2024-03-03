from openoperator import OpenOperator
from openoperator.services import AzureBlobStore, UnstructuredDocumentLoader, PGVectorStore, KnowledgeGraph, OpenAIEmbeddings, OpenaiLLM, Postgres, Timescale 
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

  # Create the different modules that are needed for the operator
  blob_store = AzureBlobStore()
  document_loader = UnstructuredDocumentLoader()
  embeddings = OpenAIEmbeddings()
  postgres = Postgres()
  vector_store = PGVectorStore(postgres=postgres, embeddings=embeddings)
  timescale = Timescale(postgres=postgres)
  knowledge_graph = KnowledgeGraph()
  llm = OpenaiLLM(model_name="gpt-4-0125-preview", system_prompt=llm_system_prompt)

  operator = OpenOperator(
    blob_store=blob_store,
    document_loader=document_loader,
    vector_store=vector_store,
    timescale=timescale,
    embeddings=embeddings,
    knowledge_graph=knowledge_graph,
    llm=llm,
    base_uri="https://syyclops.com/"
  )

  user = operator.user(email="example@example.com", password="test_password", full_name="Example Full Name")
  portfolio = operator.portfolio(user, portfolio_uri)

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
    for response in operator.chat(messages, portfolio=portfolio, verbose=verbose):
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