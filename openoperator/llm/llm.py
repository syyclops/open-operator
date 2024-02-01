from typing import List
from abc import ABC, abstractmethod
        
class LLM(ABC):
    @abstractmethod
    def __init__(self, 
                 model_name: str,
                 system_prompt: str | None = None,
                 temperature: float = 0,
                ) -> None:
        pass


    @abstractmethod
    def chat(self, messages, tools = [], available_functions = {}, verbose: bool = False):
        pass


