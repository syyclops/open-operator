from .audio import Audio
from io import BytesIO
import os
from openai import OpenAI

class OpenaiAudio(Audio):
  def __init__(self, 
    openai_api_key: str | None = None
  ) -> None:
    # Create openai client
    if openai_api_key is None:
      openai_api_key = os.environ['OPENAI_API_KEY']
    self.openai = OpenAI(api_key=openai_api_key)

  def transcribe(self, audio: BytesIO) -> str:
    try:
      transcript = self.openai.audio.transcriptions.create(
        model="whisper-1",
        file=audio,
      )

      return transcript.text
    except Exception as e:
      raise e