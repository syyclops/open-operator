from openoperator import OpenOperator

from typing import Generator, Literal
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import uvicorn

from dotenv import load_dotenv
load_dotenv()

class Message(BaseModel):
    content: str
    role: Literal['user', 'assistant']

operator = OpenOperator()

app = FastAPI()

@app.post("/chat")
async def chat(messages: list[Message], portfolio_id: str, building_id: str | None = None) -> StreamingResponse:
    messages_dict_list = [message.model_dump() for message in messages]

    async def event_stream() -> Generator[str, None, None]:
        for response in operator.chat(messages=messages_dict_list, portfolio_id=portfolio_id, building_id=building_id):
            yield response
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/files/upload")
async def upload_file(file: UploadFile, portfolio_id: str, building_id: str | None = None):
    try:
        file_content = await file.read()
        operator.files.upload_file(file_content=file_content, file_name=file.filename, portfolio_id=portfolio_id, building_id=building_id)
        return "File uploaded successfully"
    except Exception as e:
        return {"message": "There was an error uploading the file"}


if __name__ == "__main__":
    uvicorn.run(app, port=8080, host="0.0.0.0")