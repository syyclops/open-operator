from openoperator.assistant import assistant

def main():
    messages = []

    while True:
        # Get input from user
        user_input = input("Enter input: ")

        messages.append({
            "role": "user",
            "content": user_input
        })

        content = assistant.chat(messages, verbose=True)

        messages.append({
            "role": "assistant",
            "content": content
        })

        print()


if __name__ == "__main__":
    main()