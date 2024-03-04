from abc import ABC, abstractmethod
from openoperator.domain.model import Tool
from openoperator.types import LLMChatResponse
from typing import List, Generator

class LLM(ABC):
  """This is a base class for all language models. It defines the interface for interacting with language models."""
  @abstractmethod
  def __init__(
    self, 
    system_prompt: str,
    model_name: str,
    temperature: float = 0,
  ) -> None:
    pass

  @abstractmethod
  def chat(self, messages, tools: List[Tool] | None = None, verbose: bool = False) -> Generator[LLMChatResponse, None, None]:
    """Interact with the llm."""