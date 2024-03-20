from openai import OpenAI
import os
import tiktoken
import json
from typing import Generator, List
from openoperator.utils import split_string_with_limit, num_tokens_from_string
from openoperator.domain.model import LLMChatResponse, Tool, Message
from .llm import LLM

class OpenaiLLM(LLM):
  def __init__(self, 
    system_prompt: str,
    openai_api_key: str | None = None,
    model_name: str = "gpt-4",
    temperature: float = 0,
    base_url: str | None = None
  ) -> None:
    # Create openai client
    if openai_api_key is None:
      openai_api_key = os.environ['OPENAI_API_KEY']
    self.openai = OpenAI(api_key=openai_api_key, base_url=base_url)

    self.model_name = model_name
    self.temperature = temperature
    self.system_prompt = system_prompt

  def chat(self, messages: List[Message], tools: List[Tool] | None = None, verbose: bool = False) -> Generator[LLMChatResponse, None, None]:
    # Add the system message to be the first message
    messages.insert(0, Message(role="system", content=self.system_prompt))

    available_functions = {tool.name: tool.function for tool in tools} if tools else {}
    formatted_tools = [tool.get_json_schema() for tool in tools] if tools else None

    # Check messages to make sure it doesn't exceed the token limit
    messages_string = "".join([message.content for message in messages])
    messages_token_count = num_tokens_from_string(string=messages_string, encoding_name="cl100k_base")
    print("TOKEN COUNT:")
    print(messages_token_count)

    if messages_token_count > 120000:
      raise ValueError(f"The combined messages token count exceeds the limit of 120,000 tokens with {messages_token_count} tokens. Please reduce the number of messages.")
    
    while True:
      # Send the conversation and available functions to the model
      stream = self.openai.chat.completions.create(
        model=self.model_name,
        messages=[message.model_dump() for message in messages],
        tools=formatted_tools,
        tool_choice="auto" if tools else None,
        stream=True,
        temperature=self.temperature
      )

      tool_calls = []
      content = ""

      for chunk in stream:
        delta = chunk.choices[0].delta
        finish_reason = chunk.choices[0].finish_reason

        # If delta has tool calls add them to the list
        if delta.tool_calls:
          for tool_call in delta.tool_calls:
              # If the tool_call index is greater than the length of tool_calls, append new tool calls
            while len(tool_calls) <= tool_call.index:
              tool_calls.append({
                  "function": {
                      "name": "",
                      "arguments": "",
                  },
                  "id": "",
                  "type": "function"
              })

            # Update the tool call at the correct index
            tc = tool_calls[tool_call.index]
            if tool_call.id:
              tc["id"] += tool_call.id
            if tool_call.function.name:
              tc["function"]["name"] += tool_call.function.name
            if tool_call.function.arguments:
              tc["function"]["arguments"] += tool_call.function.arguments
            
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
            function_to_call = available_functions.get(function_name)
            if verbose: print(tool_call['function']['arguments'])
            function_args = json.loads(tool_call['function']['arguments'])
            if verbose: print("Tool args: " + str(function_args))

            yield LLMChatResponse(type="tool_selected", tool_id=tool_call['id'], tool_name=function_name, tool_args=function_args)
            function_response = function_to_call(function_args)
            yield LLMChatResponse(type="tool_finished", tool_id=tool_call['id'], tool_name=function_name, tool_response=function_response)

            limit = {
              "gpt-4-0125-preview": 40000,
              "gpt-4": 7000,
              "gpt-3.5-turbo": 1200
            }
            texts = split_string_with_limit(str(function_response), limit[self.model_name] or 7000, encoding)

            if verbose:
              print("Tool response:")
              print(function_response)

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
          yield LLMChatResponse(content=delta.content or "", type="content")
          return

        # Update the content with the delta content
        if delta.content:
          content += delta.content

        # If there are no tool calls and just streaming a normal response then print the chunks
        if not tool_calls:
          yield LLMChatResponse(content=delta.content or "", type="content")