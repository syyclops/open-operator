from abc import ABC, abstractmethod
        
class AI(ABC):
    """
    This is the abse class for all AI methods and models.

    1. Chat
    2. Transcribe (speech to text)
    """
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

    @abstractmethod
    def transcribe(self, audio) -> str:
        pass


