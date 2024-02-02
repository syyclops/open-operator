from openoperator import OpenOperator
from openoperator.blob_store import AzureBlobStore
from openoperator.document_loader import UnstructuredDocumentLoader
from openoperator.vector_store import PGVectorStore
from openoperator.embeddings import OpenAIEmbeddings
from openoperator.knowledge_graph import KnowledgeGraph
from openoperator.llm import OpenAILLM

import argparse
from dotenv import load_dotenv
load_dotenv()


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--portfolio_uri', type=str, help='The portfolio ID to use for the chat', default="https://openoperator.com/setty%20%26%20associates")
    parser.add_argument('--verbose', type=bool, default=False, help='Print verbose output') 
    args = parser.parse_args()
    verbose = args.verbose
    portfolio_uri = args.portfolio_uri

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

    portfolio = operator.portfolio(portfolio_uri)

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
            content = response
            print(content, flush=True, end="")

        messages.append({
            "role": "assistant",
            "content": content
        })

        print()


if __name__ == "__main__":
    main()