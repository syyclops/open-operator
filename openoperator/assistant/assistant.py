from ..db import vector_store
from openai import OpenAI
import json

class Assistant: 
    def __init__(self) -> None:
        # State
        self.client = OpenAI(api_key="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")

        self.system_prompt = """You are an an AI Assistant that specializes in building operations and maintenance.
Your goal is to help facility owners, managers, and operators manage their facilities and buildings more efficiently.
Make sure to always follow ASHRAE guildelines.
Don't be too wordy. Don't be too short. Be just right.
Don't make up information. If you don't know, say you don't know.
Always responsd with markdown formatted text."""

        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

        # Define tools to give model
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_building_documents",
                    "description": "Search building documents for metadata. These documents are drawings/plans, O&M manuals, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to use.",
                            },
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

    
    def search_building_documents(self, query: str) -> str:
        """Search building documents for metadata. These documents are drawings/plans, O&M manuals, etc."""
        docs = vector_store.similarity_search(query, 8)

        return str(docs)
    
    def chat(self, input: str):
        print(input)
        # Add user input to messages
        self.messages.append({"role": "user", "content": input})

        # Step 1: send the conversation and available functions to the model
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            tools=self.tools,
            tool_choice="auto",  # auto is default, but we'll be explicit
        )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                "search_building_documents": self.search_building_documents,
            }  # only one function in this example, but you can have multiple
            self.messages.append(response_message)  # extend conversation with assistant's reply
            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(
                    function_args['query'],
                )
                self.messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )  # extend conversation with function response

            stream = self.client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=self.messages,
                stream=True
            )  # get a new response from the model where it can see the function response

            for chunk in stream:
                print(chunk.choices[0].delta.content or "", end="")
        else:
            return response_message.content