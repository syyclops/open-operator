from openoperator import OpenOperator
from dotenv import load_dotenv
load_dotenv()


def main():
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

        content = operator.chat(messages, verbose=True)

        messages.append({
            "role": "assistant",
            "content": content
        })

        print()


if __name__ == "__main__":
    main()