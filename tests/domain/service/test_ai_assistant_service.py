import unittest
from unittest.mock import Mock 
from openoperator.domain.service import AIAssistantService
from openoperator.domain.model import Message
from typing import List

class TestAIAssistantService(unittest.TestCase):
  def setUp(self):
    self.knowledge_graph = Mock()
    self.llm = Mock()
    document_repository = Mock()
    self.document_repository = document_repository
    self.ai_assistant_service = AIAssistantService(llm=self.llm, document_repository=document_repository)
    self.portfolio_uri = "https://openoperator.com/portfolio"
    self.facility_uri = "https://openoperator.com/exampleCustomer/exampleFacility"
        
  def test_chat(self):
    self.llm.chat.return_value = iter(["AI response to search for documents"])

    # Define the messages to simulate user interaction
    messages: List[Message] = [
      Message(content="Search for documents", role="user")
    ]

    # Execute the chat function
    responses = list(self.ai_assistant_service.chat(portfolio_uri=self.portfolio_uri, messages=messages))

    # Verify
    self.llm.chat.assert_called_once()  # Ensure the AI chat was called
    self.assertEqual(len(responses), 1)  # Check if there is one response
    self.assertEqual(responses[0], "AI response to search for documents")  # Validate the response content

  def test_chat_with_ai_error(self):
    self.llm.chat.side_effect = Exception("AI error")

    # Define the messages to simulate user interaction
    messages: List[Message] = [
      Message(content="Search for documents", role="user")
    ]

    # Execute the chat function
    with self.assertRaises(Exception) as context:
      list(self.ai_assistant_service.chat(portfolio_uri=self.portfolio_uri, messages=messages))

    self.assertTrue("AI error" in str(context.exception))


if __name__ == '__main__':
  unittest.main()