from unittest.mock import Mock, patch, MagicMock
from openoperator.services import Openai 
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice, ChoiceDelta

# Test initialization with default parameters
def test_openai_init_defaults():
    with patch('openoperator.services.ai.openai.os') as mock_os:
        mock_os.environ = {'OPENAI_API_KEY': 'test_key'}
        openai_instance = Openai()
        assert openai_instance.model_name == "gpt-4"
        assert openai_instance.temperature == 0
        assert 'You are an an AI Assistant' in openai_instance.system_prompt

# Test initialization with custom parameters
def test_openai_init_custom():
    custom_prompt = "Custom system prompt."
    openai_instance = Openai(
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
@patch('openoperator.services.ai.openai.OpenAI')  # Mock the OpenAI client
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

    ai = Openai(openai_api_key="dummy_key")
    messages = [{"role": "user", "content": "Hello, AI"}]

    for response in ai.chat(messages):
        assert response == "Test response"

    mock_openai_instance.chat.completions.create.assert_called_once()