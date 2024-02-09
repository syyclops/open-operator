from openoperator import OpenOperator
from openoperator.services.blob_store import AzureBlobStore
from openoperator.services.document_loader import UnstructuredDocumentLoader
from openoperator.services.vector_store import PGVectorStore
from openoperator.services.embeddings import OpenAIEmbeddings
from openoperator.services.knowledge_graph import KnowledgeGraph
from openoperator.services.ai import Openai

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
    ai = Openai(model_name="gpt-4-0125-preview")

    operator = OpenOperator(
        blob_store=blob_store,
        document_loader=document_loader,
        vector_store=vector_store,
        embeddings=embeddings,
        knowledge_graph=knowledge_graph,
        ai=ai,
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
            content = response
            print(content, flush=True, end="")

        messages.append({
            "role": "assistant",
            "content": content
        })

        print()


if __name__ == "__main__":
    main()