from unittest.mock import Mock, patch, MagicMock
from openoperator.services import OpenaiLLM 
from openoperator.core.tool import Tool, ToolParametersSchema
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice, ChoiceDelta, ChoiceDeltaToolCall, ChoiceDeltaToolCallFunction
from openoperator.types import AiChatResponse, ToolCall, ToolResponse

# Test initialization with default parameters
def test_openai_init_defaults():
  with patch('openoperator.services.llm.openai_llm.os') as mock_os:
    mock_os.environ = {'OPENAI_API_KEY': 'test_key'}
    system_prompt = "You are an an AI Assistant"
    openai_instance = OpenaiLLM(system_prompt=system_prompt)
    assert openai_instance.model_name == "gpt-4"
    assert openai_instance.temperature == 0
    assert 'You are an an AI Assistant' in openai_instance.system_prompt

# Test initialization with custom parameters
def test_openai_init_custom():
  custom_prompt = "Custom system prompt."
  openai_instance = OpenaiLLM(
    openai_api_key="custom_key",
    system_prompt=custom_prompt,
    model_name="custom-model",
    temperature=0.5,
    base_url="https://custom.api"
  )
  assert openai_instance.openai.api_key == "custom_key"
  assert openai_instance.system_prompt == custom_prompt
  assert openai_instance.model_name == "custom-model"
  assert openai_instance.temperature == 0.5
  assert openai_instance.openai.base_url == "https://custom.api"

# Test the chat method with mocked OpenAI response
@patch('openoperator.services.llm.openai_llm.OpenAI')  # Mock the OpenAI client
def test_openai_chat(mock_openai):
  # Setup the mock response to simulate an iterable of response objects
  delta = ChoiceDelta(content="Test response", role="assistant")
  choice = Choice(delta=delta, finish_reason="stop", index=0)
  chunk = ChatCompletionChunk(choices=[choice], created=0, model='gpt-4', system_fingerprint='test', object='chat.completion.chunk', id='test')

  # Create an iterator over a list containing the mock response
  mock_stream = iter([chunk])
  
  mock_openai_instance = MagicMock()
  mock_openai_instance.chat.completions.create.return_value = mock_stream
  mock_openai.return_value = mock_openai_instance

  ai = OpenaiLLM(openai_api_key="dummy_key")
  messages = [{"role": "user", "content": "Hello, AI"}]

  for response in ai.chat(messages):
    assert response == AiChatResponse(content="Test response", tool_finished=None, tool_selected=None)

  mock_openai_instance.chat.completions.create.assert_called_once()

@patch('openoperator.services.llm.openai_llm.OpenAI')
def test_openai_chat_multiple_chunks(mock_openai):
  # Setup mock response to simulate multiple chunks
  delta_chunk1 = ChoiceDelta(content="Part 1 ", role="assistant")
  delta_chunk2 = ChoiceDelta(content="Part 2", role="assistant")
  choice1 = Choice(delta=delta_chunk1, index='0')
  choice2 = Choice(delta=delta_chunk2, finish_reason="stop", index='1')
  chunk1 = ChatCompletionChunk(choices=[choice1], created=0, model='gpt-4', system_fingerprint='test', object='chat.completion.chunk', id='chunk1')
  chunk2 = ChatCompletionChunk(choices=[choice2], created=0, model='gpt-4', system_fingerprint='test2', object='chat.completion.chunk', id='chunk2')

  mock_stream = iter([chunk1, chunk2])
  
  mock_openai_instance = MagicMock()
  mock_openai_instance.chat.completions.create.return_value = mock_stream
  mock_openai.return_value = mock_openai_instance

  ai = OpenaiLLM(openai_api_key="dummy_key")
  messages = [{"role": "user", "content": "Need a longer response"}]

  full_response = ""
  for response in ai.chat(messages):
    full_response += response.content

  assert full_response == "Part 1 Part 2"

  assert mock_openai_instance.chat.completions.create.call_count == 1

@patch('openoperator.services.llm.openai_llm.OpenAI')
def test_openai_chat_with_tools(mock_openai):
  # Mock Openai response with tool calls 
  function = ChoiceDeltaToolCallFunction(name="test_function", arguments="{\"query\": \"test\"}")
  tool_call = ChoiceDeltaToolCall(index=0, type="function", function=function)
  delta = ChoiceDelta(role="assistant", tool_calls=[tool_call], content="")
  choice = Choice(delta=delta, index=0)
  chunk1 = ChatCompletionChunk(choices=[choice], created=0, model='gpt-4', system_fingerprint='test', object='chat.completion.chunk', id='test')

  delta2 = ChoiceDelta(content=None, role="assistant")
  choice2 = Choice(delta=delta2, index=0, finish_reason="tool_calls")
  chunk2 = ChatCompletionChunk(choices=[choice2], created=0, model='gpt-4', system_fingerprint='test', object='chat.completion.chunk', id='test')

  mock_stream = iter([chunk1, chunk2])

  # Mock openai response after tool call
  delta3 = ChoiceDelta(content="Test function", role="assistant") 
  choice3 = Choice(delta=delta3, index=0, finish_reason="stop")
  chunk3 = ChatCompletionChunk(choices=[choice3], created=0, model='gpt-4', system_fingerprint='test', object='chat.completion.chunk', id='test')
  
  mock_openai_instance = MagicMock()
  mock_openai_instance.chat.completions.create.side_effect = [mock_stream, iter([chunk3])]
  mock_openai.return_value = mock_openai_instance

  ai = OpenaiLLM(openai_api_key="dummy_key")
  messages = [{"role": "user", "content": "Hello, AI"}]   

  document_search_parameters: ToolParametersSchema = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The search query to use.",
        },
    },
    "required": ["query"],
  }
  document_search_tool = Tool(name="test_function", description="Search documents for metadata. These documents are drawings/plans, O&M manuals, etc.", function=Mock(return_value=[{"content": "Test function"}]), parameters_schema=document_search_parameters)
  tools = [document_search_tool]

  responses = []

  for response in ai.chat(messages, tools):
    responses.append(response)

  assert responses[0] == AiChatResponse(content=None, tool_selected=ToolCall(function_name="test_function", arguments={"query": "test"}), tool_finished=None)
  assert responses[1] == AiChatResponse(content=None, tool_selected=None, tool_finished=ToolResponse(name="test_function", content=[{"content": "Test function"}]))
  assert responses[2] == AiChatResponse(content="Test function", tool_selected=None, tool_finished=None)
  assert len(responses) == 3
  assert mock_openai_instance.chat.completions.create.call_count == 2