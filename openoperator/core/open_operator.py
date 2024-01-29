from .files.files import Files
from openai import OpenAI
import json
import tiktoken
import os
from typing import List
from ..services.graph_db import GraphDB
from ..services.blob_store import BlobStore
from ..services.embeddings import Embeddings
from ..services.document_loader import DocumentLoader
from ..services.vector_store import VectorStore
from .cobie.cobie import COBie

class OpenOperator: 
    """
    This class (one instance is called 'operator') is the center of this project.

    Its responsibilities are:

    - Provide a chat method that can be used to interact with the assistant
    - Provide a files object that can be used to upload files to the assistant
    - Provide a knowledge graph object that can be used to interact with the knowledge graph of the assistant
    """
    def __init__(
        self, 
        postgres_connection_string: str | None = None, 
        postgres_embeddings_table: str | str = None, 
        openai_api_key: str | None = None,
        unstructured_api_key: str | None = None,
        unstructured_api_url: str | None = None,
        neo4j_uri: str | None = None,
        neo4j_user: str | None = None,
        neo4j_password: str | None = None,
        container_client_connection_string: str | None = None,
        container_name: str | None = None,
    ) -> None:
        # Services
        blob_store = BlobStore(container_client_connection_string=container_client_connection_string, container_name=container_name)
        graph_db = GraphDB(neo4j_uri=neo4j_uri, neo4j_user=neo4j_user, neo4j_password=neo4j_password)
        embeddings = Embeddings(openai_api_key=openai_api_key)
        document_loader = DocumentLoader(unstructured_api_key=unstructured_api_key, unstructured_api_url=unstructured_api_url)
        vector_store = VectorStore(embeddings=embeddings, collection_name=postgres_embeddings_table, connection_string=postgres_connection_string)
        
        # Core modules
        self.files = Files(blob_store=blob_store, vector_store=vector_store, document_loader=document_loader)
        self.cobie = COBie(graph_db=graph_db, blob_store=blob_store)

        # Create openai client
        if openai_api_key is None:
            openai_api_key = os.environ['OPENAI_API_KEY']
        self.openai = OpenAI(api_key=openai_api_key)

        self.system_prompt = """You are an an AI Assistant that specializes in building operations and maintenance.
Your goal is to help facility owners, managers, and operators manage their facilities and buildings more efficiently.
Make sure to always follow ASHRAE guildelines.
Don't be too wordy. Don't be too short. Be just right.
Don't make up information. If you don't know, say you don't know.
Always respond with markdown formatted text."""

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

    def chat(self, messages, portfolio_id: str, building_id: bool = False, verbose: bool = False):
        # Add the system message to be the first message
        messages.insert(0, {
            "role": "system",
            "content": self.system_prompt
        })

        available_functions = {
            "search_building_documents": self.files.search_metadata,
        }

        while True:
            # Send the conversation and available functions to the model
            stream = self.openai.chat.completions.create(
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
                        if verbose: print("Tool Selected: " + function_name)
                        function_to_call = available_functions[function_name]
                        function_args = json.loads(tool_call['function']['arguments'])
                        if verbose: print("Tool args: " + str(function_args))
                        filter = {
                            "portfolio_id": portfolio_id
                        }
                        if building_id:
                            filter["building_id"] = building_id
                        function_response = function_to_call(
                            function_args['query'],
                            8,
                            filter=filter
                        )

                        # Convert function response to string and limit to 5000 tokens
                        encoding = tiktoken.get_encoding("cl100k_base")
                        texts = split_string_with_limit(str(function_response), 5000, encoding)

                        if verbose: print("Tool response: " + texts[0])

                        # Extend conversation with function response
                        messages.append(
                            {
                                "tool_call_id": tool_call['id'],
                                "role": "tool",
                                "name": function_name,
                                "content": texts[0]
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




def split_string_with_limit(text: str, limit: int, encoding) -> List[str]:
    """
    Splits a string into multiple parts with a limit on the number of tokens in each part.
    """
    tokens = encoding.encode(text)
    parts = []
    current_part = []
    current_count = 0

    for token in tokens:
        current_part.append(token)
        current_count += 1

        if current_count >= limit:
            parts.append(current_part)
            current_part = []
            current_count = 0

    if current_part:
        parts.append(current_part)

    text_parts = [encoding.decode(part) for part in parts]

    return text_parts
