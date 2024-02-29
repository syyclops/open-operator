from abc import ABC, abstractmethod

class Audio(ABC):
  @abstractmethod
  def transcribe(self, audio) -> str:
    """
    Transcribe audio to text.
    """