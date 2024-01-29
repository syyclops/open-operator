from openoperator import OpenOperator
import argparse
from dotenv import load_dotenv
load_dotenv()


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', type=bool, default=False, help='Print verbose output') 
    args = parser.parse_args()
    verbose = args.verbose

    operator = OpenOperator()

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

        content = operator.chat(messages, portfolio_id="test", verbose=verbose)

        messages.append({
            "role": "assistant",
            "content": content
        })

        print()


if __name__ == "__main__":
    main()