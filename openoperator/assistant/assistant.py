from .files.files import Files
from openai import OpenAI
import json

class Assistant: 
    def __init__(self) -> None:
        self.files = Files(self)

        self.client = OpenAI()

        self.system_prompt = """You are an an AI Assistant that specializes in building operations and maintenance.
Your goal is to help facility owners, managers, and operators manage their facilities and buildings more efficiently.
Make sure to always follow ASHRAE guildelines.
Don't be too wordy. Don't be too short. Be just right.
Don't make up information. If you don't know, say you don't know.
Always responsd with markdown formatted text."""

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


    def chat(self, messages, verbose: bool = False):
        # Add the system message to be the first message
        messages.insert(0, {
            "role": "system",
            "content": self.system_prompt
        })

        available_functions = {
            "search_building_documents": self.files.similarity_search,
        }

        while True:

            # Send the conversation and available functions to the model
            stream = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                stream=True
            )

            tool_calls = []
            content = ""

            for chunk in stream:
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                # If delta has tool calls add them to the list
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        # If tool_calls is empty then add the first tool call
                        if not tool_calls:
                            tool_calls.append({
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                                "id": tool_call.id,
                                "type": tool_call.type
                            })
                            continue
        
                    # If tool_calls is not empty then update the tool call if it already exists
                    tool_calls[0]['function']['arguments'] += tool_call.function.arguments

                    
                # If the stream is done and is ready to use tools
                if finish_reason == "tool_calls":
                    # Extend the conversation with the assistant's reply
                    messages.append({
                        "role": "assistant",
                        "content": content,
                        "tool_calls": tool_calls
                    })

                    for tool_call in tool_calls:
                        function_name = tool_call['function']['name']
                        if verbose:
                            print("Tool Selected: " + function_name)

                        function_to_call = available_functions[function_name]
                        function_args = json.loads(tool_call['function']['arguments'])
                        function_response = function_to_call(
                            function_args['query'],
                            5
                        )

                        # Convert function response to string and limit to 4000 characters
                        function_response = str(function_response)[:4000]

                        if verbose:
                            print("Tool response: " + function_response)

                        # Extend conversation with function response
                        messages.append(
                            {
                                "tool_call_id": tool_call['id'],
                                "role": "tool",
                                "name": function_name,
                                "content": function_response 
                            }
                        )

                # If the stream is done because its the end of the conversation then return
                if finish_reason == "stop":
                    return content

                # Update the content with the delta content
                if delta.content:
                    content += delta.content

                # If there are no tool calls and just streaming a normal response then print the chunks
                if not tool_calls:
                    print(delta.content or "", end="", flush=True)