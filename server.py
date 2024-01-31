from openoperator import OpenOperator

from typing import Generator, Literal
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse, Response, FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from dotenv import load_dotenv
load_dotenv()

class Message(BaseModel):
    content: str
    role: Literal['user', 'assistant']

operator = OpenOperator()

app = FastAPI(title="Open Operator API")

@app.post("/chat", tags=["assistant"])
async def chat(messages: list[Message], portfolio_id: str, building_id: str | None = None) -> StreamingResponse:
    messages_dict_list = [message.model_dump() for message in messages]

    async def event_stream() -> Generator[str, None, None]:
        for response in operator.chat(messages=messages_dict_list, portfolio_id=portfolio_id, building_id=building_id):
            yield response
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/files/upload", tags=['files'])
async def upload_file(file: UploadFile, portfolio_id: str, building_id: str | None = None):
    try:
        file_content = await file.read()
        operator.files.upload_file(file_content=file_content, file_name=file.filename, portfolio_idA=portfolio_id, building_id=building_id)
        return "File uploaded successfully"
    except Exception as e:
        return Response(content=str(e), status_code=500) 
    
@app.post("/cobie/validate_spreadsheet", tags=['cobie'])
async def validate_spreadsheet(file: UploadFile, download_update_file: bool):
    try:
        file_content = await file.read()
        errors_founds, errors, updated_file_path = operator.cobie.validate_spreadsheet(file_content)
        if errors_founds:
            if download_update_file:
                return FileResponse(updated_file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="updated_cobie.xlsx")
            else:
                return JSONResponse(content=errors)
        else:
            return {"message": "No errors found"}
    except Exception as e:
        print(e)
        return Response(content="Unable to validate spreadsheet", status_code=500)


@app.get("/portfolio/list", tags=['portfolio'])
async def list_portfolios() -> JSONResponse:
    return JSONResponse(operator.portfolios())

@app.post("/portfolio/create", tags=['portfolio'])
async def create_portfolio(portfolio_name: str) -> JSONResponse:
    portfolio = operator.create_portfolio(portfolio_name)
    return JSONResponse(portfolio)

@app.get("/portfolio/{portfolio_id}/facilities", tags=['portfolio'])
async def list_buildings(portfolio_id: str) -> JSONResponse:
    return JSONResponse(operator.portfolio(portfolio_id).list_buildings())

@app.post("/portfolio/{portfolio_id}/facility/create", tags=['portfolio'])
async def create_building(portfolio_id: str, building_name: str) -> JSONResponse:
    return JSONResponse(operator.portfolio(portfolio_id).create_building(building_name))

# if __name__ == "__main__":
#     uvicorn.run(app, port=8080, host="0.0.0.0")