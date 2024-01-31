from openoperator import OpenOperator
from openoperator import BlobStore
from openoperator import DocumentLoader
from openoperator import VectorStore
from openoperator import Embeddings
from openoperator import KnowledgeGraph
from openoperator import LLM
from openoperator import COBie

from typing import Generator, Literal
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse, Response, FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import mimetypes

from dotenv import load_dotenv
load_dotenv()

class Message(BaseModel):
    content: str
    role: Literal['user', 'assistant']

# Create the different modules that are needed for the operator
blob_store = BlobStore()
document_loader = DocumentLoader() # used to extract text from documents
embeddings = Embeddings()
vector_store = VectorStore(embeddings=embeddings)
knowledge_graph = KnowledgeGraph()
llm = LLM(model_name="gpt-4-0125-preview")

operator = OpenOperator(
    blob_store=blob_store,
    document_loader=document_loader,
    vector_store=vector_store,
    embeddings=embeddings,
    knowledge_graph=knowledge_graph,
    llm=llm
)

app = FastAPI(title="Open Operator API")

@app.post("/chat", tags=["assistant"])
async def chat(messages: list[Message], portfolio_id: str, facility_id: str | None = None) -> StreamingResponse:
    messages_dict_list = [message.model_dump() for message in messages]

    portfolio = operator.portfolio(portfolio_id)
    facility = None
    if facility_id:
        facility = portfolio.facility(facility_id=facility_id)

    async def event_stream() -> Generator[str, None, None]:
        for response in operator.chat(messages=messages_dict_list, portfolio=portfolio, facility=facility):
            yield response
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/files/upload", tags=['files'])
async def upload_file(file: UploadFile, portfolio_id: str, facility_id: str | None = None):
    try:
        file_content = await file.read()
        file_type = mimetypes.guess_type(file.filename)[0]
        operator.portfolio(portfolio_id).facility(facility_id=facility_id).upload_document(file_content=file_content, file_name=file.filename, file_type=file_type)
        return "File uploaded successfully"
    except Exception as e:
        print(e)
        return Response(content=str(e), status_code=500) 
    
@app.post("/cobie/validate_spreadsheet", tags=['cobie'])
async def validate_spreadsheet(file: UploadFile, download_update_file: bool):
    try:
        file_content = await file.read()
        spreadsheet = COBie(file_content)
        errors_founds, errors, updated_file_path = spreadsheet.validate_spreadsheet()
        if errors_founds:
            if download_update_file:
                return FileResponse(updated_file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="updated_cobie.xlsx")
            else:
                return JSONResponse(content=errors)
        else:
            return {"message": "No errors found"}
    except Exception as e:
        print(e)
        return Response(content=f"Unable to validate spreadsheet: {e}", status_code=500)


@app.get("/portfolio/list", tags=['portfolio'])
async def list_portfolios() -> JSONResponse:
    return JSONResponse(operator.portfolios())

@app.post("/portfolio/create", tags=['portfolio'])
async def create_portfolio(portfolio_name: str) -> JSONResponse:
    portfolio = operator.create_portfolio(portfolio_name)
    return JSONResponse(portfolio.details())

@app.get("/portfolio/{portfolio_id}/facilities", tags=['portfolio'])
async def list_buildings(portfolio_id: str) -> JSONResponse:
    try:
        return JSONResponse(operator.portfolio(portfolio_id).list_buildings())
    except Exception as e:
        return Response(content="Unable to create portfolio", status_code=500)

@app.post("/portfolio/{portfolio_id}/facility/create", tags=['portfolio'])
async def create_facility(portfolio_id: str, building_name: str) -> JSONResponse:
    return JSONResponse(operator.portfolio(portfolio_id).create_facility(building_name).details())

# if __name__ == "__main__":
#     uvicorn.run(app, port=8080, host="0.0.0.0")