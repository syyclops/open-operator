from openoperator.assistant import assistant

def main():
    # Get input from user
    user_input = input("Enter input: ")

    response = assistant.chat(user_input)

    print(response)



if __name__ == "__main__":
    main()