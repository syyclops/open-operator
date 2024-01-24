from openoperator import OpenOperator
from openoperator.open_operator import split_string_with_limit 
import tiktoken

def test_split_string_with_limit():
    text = 'Space: The final frontier'
    limit = 4
    
    encoding = tiktoken.get_encoding("cl100k_base")
    split_text = split_string_with_limit(text, limit, encoding)
    assert split_text == ['Space: The final', ' frontier']

def test_open_operator_init(mocker):
    # Mock environment variables and dependencies
    mocker.patch('os.environ', {
        'OPENAI_API_KEY': 'dummy_key', 
        'POSTGRES_CONNECTION_STRING': 'postgresql://myusername:mypassword@localhost/mydatabase', 
        'POSTGRES_EMBEDDINGS_TABLE': 'dummy_table', 
        'UNSTRUCTURED_API_KEY': 'dummy_unstructured_key', 
        'UNSTRUCTURED_URL': 'dummy_url'
    })

    # Mock OpenAI and other external classes
    mocker.patch('openoperator.vector_store.VectorStore.__init__', return_value=None)

    # Create an instance of the class
    operator = OpenOperator()

    # Assertions to ensure everything was called correctly
    assert operator.openai is not None
    assert operator.system_prompt is not None
    assert operator.files is not None
