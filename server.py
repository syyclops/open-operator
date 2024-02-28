import mimetypes
from typing import Generator, List
from fastapi import FastAPI, UploadFile, Depends, Security, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from io import BytesIO
import os
import json
from openoperator.types import DocumentQuery, Message, TimeseriesReading, PortfolioModel, LLMChatResponse, Transcription, DocumentModel, DocumentMetadataChunk
from openoperator.core import User, OpenOperator
from openoperator.services import AzureBlobStore, UnstructuredDocumentLoader, PGVectorStore, KnowledgeGraph, OpenAIEmbeddings, OpenaiLLM, Postgres, Timescale, OpenaiAudio
from dotenv import load_dotenv
load_dotenv()

llm_system_prompt = """You are an an AI Assistant that specializes in building operations and maintenance.
Your goal is to help facility owners, managers, and operators manage their facilities and buildings more efficiently.
Make sure to always follow ASHRAE guildelines.
Don't be too wordy. Don't be too short. Be just right.
Don't make up information. If you don't know, say you don't know.
Always respond with markdown formatted text."""

# Create the different modules that are needed for the operator
blob_store = AzureBlobStore()
document_loader = UnstructuredDocumentLoader()
embeddings = OpenAIEmbeddings()
postgres = Postgres()
vector_store = PGVectorStore(postgres=postgres, embeddings=embeddings)
timescale = Timescale(postgres=postgres)
knowledge_graph = KnowledgeGraph()
llm = OpenaiLLM(model_name="gpt-4-0125-preview", system_prompt=llm_system_prompt)
audio = OpenaiAudio()

operator = OpenOperator(
  blob_store=blob_store,
  document_loader=document_loader,
  vector_store=vector_store,
  timescale=timescale,
  embeddings=embeddings,
  knowledge_graph=knowledge_graph,
  llm=llm,
  audio=audio,
  base_uri="https://syyclops.com/"
)

app = FastAPI(title="Open Operator API")
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
  # If its local development, return a dummy user
  if os.environ.get("ENV") == "dev":
    return User(operator, email="example@example.com", password="", full_name="Example User")
  token = credentials.credentials
  try:
    user = operator.get_user_from_access_token(token)
    return user
  except HTTPException as e:
    raise e

@app.post("/signup", tags=["Auth"])
async def signup(email: str, password: str, full_name: str) -> JSONResponse:
  try:
    return JSONResponse(operator.user(email, password, full_name).signup())
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to create user: {e}"}, status_code=500)

@app.post("/login", tags=["Auth"])
async def login(email: str, password: str) -> JSONResponse:
  try:
    return JSONResponse(operator.user(email, password, "").login())
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to login: {e}"}, status_code=500)

@app.post("/chat", tags=["AI"], response_model=Generator[LLMChatResponse, None, None])
async def chat(
  messages: list[Message],
  portfolio_uri: str,
  facility_uri: str | None = None,
  current_user: User = Security(get_current_user)
) -> StreamingResponse:
  messages_dict_list = [message.model_dump() for message in  messages]

  portfolio = operator.portfolio(current_user, portfolio_uri)
  facility = None
  if facility_uri:
    facility = portfolio.facility(facility_uri)

  async def event_stream() -> Generator[str, None, None]:
    for response in operator.chat(
        messages=messages_dict_list,
        portfolio=portfolio,
        facility=facility
    ):
      yield json.dumps(response.model_dump())

  return StreamingResponse(event_stream(), media_type="text/event-stream")
  
@app.post("/transcribe", tags=["AI"], response_model=Transcription)
async def transcribe_audio(
  file: UploadFile,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    file_content = await file.read()
    buffer = BytesIO(file_content)
    buffer.name = file.filename
    return JSONResponse(content={"text": operator.transcribe(buffer)})
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to transcribe audio: {e}"}, status_code=500)


# @app.post("/cobie/validate_spreadsheet", tags=['cobie'])
# async def validate_spreadsheet(file: UploadFile, download_update_file: bool):
#     try:
#         file_content = await file.read()
#         # spreadsheet = COBie(file_content)
#         errors_founds, errors, updated_file = spreadsheet.validate_spreadsheet()
#         if errors_founds:
#             if download_update_file:
#                 return Response(content=updated_file, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=updated_cobie.xlsx"})
#             else:
#                 return JSONResponse(content=errors)
#         else:
#             return {"message": "No errors found"}
#     except Exception as e:
#         print(e)
#         return Response(content=f"Unable to validate spreadsheet: {e}", status_code=500)

@app.get("/portfolio/list", tags=['Portfolio'], response_model=List[PortfolioModel])
async def list_portfolios(current_user: User = Security(get_current_user)) -> JSONResponse:
  return JSONResponse([portfolio.model_dump() for portfolio in operator.portfolios(current_user)])

@app.post("/portfolio/create", tags=['Portfolio'], response_model=PortfolioModel)
async def create_portfolio(
  portfolio_name: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    portfolio = operator.create_portfolio(current_user, portfolio_name)
    return JSONResponse(portfolio.details())
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to create portfolio: {e}"}, status_code=500)

@app.get("/facilities", tags=['Portfolio'])
async def list_facilities(
  portfolio_uri: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  return JSONResponse(operator.portfolio(current_user, portfolio_uri).list_facilities())

@app.post("/facility/create", tags=['Facility'])
async def create_facility(
  portfolio_uri: str,
  building_name: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  return JSONResponse(
    operator.portfolio(current_user, portfolio_uri).create_facility(building_name).details()
  )

@app.post("/cobie/import", tags=['Facility'])
async def import_cobie_spreadsheet(
  portfolio_uri: str, 
  facility_uri: str, 
  file: UploadFile, 
  validate: bool = True,
  current_user: User = Security(get_current_user)
):
  try:
    file_content = await file.read()
    errors_found, errors = operator.portfolio(current_user, portfolio_uri).facility(facility_uri).cobie.upload_cobie_spreadsheet(file_content, validate)
    if errors_found:
      return JSONResponse(content={"errors": errors}, status_code=400)
    return "COBie spreadsheet imported successfully"
  except HTTPException as e:
    return Response(content=str(e), status_code=500)
  
## DOCUMENTS ROUTES
@app.get("/documents", tags=['Documents'], response_model=List[DocumentModel])
async def list_documents(
  portfolio_uri: str,
  facility_uri: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  return JSONResponse(
    operator.portfolio(current_user, portfolio_uri).facility(facility_uri).documents.list()
  )
  
@app.post("/documents/search", tags=['Documents'], response_model=List[DocumentMetadataChunk])
async def search_documents(
  portfolio_uri: str,
  facility_uri: str,
  query: DocumentQuery,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  return JSONResponse(
    operator.portfolio(current_user, portfolio_uri).facility(facility_uri).documents.search(query.model_dump())
  )

@app.delete("/document/delete", tags=['Documents'])
async def delete_document(
  portfolio_uri: str,
  facility_uri: str,
  document_uri: str,
  current_user: User = Security(get_current_user)
) -> Response:
  try:
    operator.portfolio(
      current_user,
      portfolio_uri
    ).facility(facility_uri).documents.delete(document_uri)
    return JSONResponse(content={
      "message": "Document deleted successfully",
    })
  except HTTPException as e:
    return JSONResponse(
      content={"message": f"Unable to delete document: {e}"},
      status_code=400
    )

@app.post("/documents/upload", tags=['Documents'])
async def upload_files(
  files: List[UploadFile],
  portfolio_uri: str,
  facility_uri: str,
  background_tasks: BackgroundTasks,
  current_user: User = Security(get_current_user),
):
  uploaded_files_info = []  # To store info about uploaded files

  for file in files:
    try:
      file_content = await file.read()
      file_type = mimetypes.guess_type(file.filename)[0]
      document = operator.portfolio(
        current_user,
        portfolio_uri
      ).facility(facility_uri).documents.upload(
        file_content=file_content,
        file_name=file.filename,
        file_type=file_type
      )

      background_tasks.add_task(operator.portfolio(
        current_user,
        portfolio_uri
      ).facility(facility_uri).documents.run_extraction_process, file_content, file.filename, document.uri, document.url)

      uploaded_files_info.append({"filename": file.filename, "uri": document.uri})
    except Exception as e:  # Catching a more general exception; you might want to log this or handle it differently
      return JSONResponse(
          content={"message": f"Unable to upload file {file.filename}: {e}"},
          status_code=500
      )

  return {"message": "Files uploaded successfully", "uploaded_files": uploaded_files_info}

### DEVICES ROUTES
@app.get("/devices", tags=['Devices'])
async def list_devices(
  portfolio_uri: str,
  facility_uri: str,
  component_uri: str | None = None,
  brick_class: str | None = None,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    devices = operator.portfolio(
      current_user, portfolio_uri
    ).facility(facility_uri).device_manager.devices(component_uri, brick_class)
    for device in devices: # Remove the embedding from the response
      device.pop('embedding', None)
    return JSONResponse(devices)
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to list devices: {e}"},
        status_code=500
    )

@app.get("/devices/cluster", tags=['Devices'])
async def list_device_cluster(
  portfolio_uri: str,
  facility_uri: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  return JSONResponse(
    operator.portfolio(
        current_user, portfolio_uri
    ).facility(facility_uri).device_manager.cluster_devices()
  )

@app.post("/devices/classify", tags=['Devices'])
async def assign_brick_class(
  portfolio_uri: str,
  facility_uri: str,
  uris: List[str] ,
  brick_class: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    operator.portfolio(
      current_user,
      portfolio_uri
    ).facility(facility_uri).device_manager.assign_brick_class(uris, brick_class)
    return JSONResponse(content={"message": "Brick class assigned successfully"})
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to assign brick class: {e}"},
        status_code=500
    )
  
@app.put("/device/update", tags=['Devices'])
async def update_device(
  portfolio_uri: str,
  facility_uri: str,
  device_uri: str,
  new_details: dict,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    operator.portfolio(
      current_user,
      portfolio_uri
    ).facility(facility_uri).device(device_uri).update(new_details)
    return JSONResponse(content={"message": "Device updated successfully"})
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to update device: {e}"},
        status_code=500
    )
  
@app.get("/device/link", tags=['Devices'])
async def link_to_component(
  portfolio_uri: str,
  facility_uri: str,
  device_uri: str,
  component_uri: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    return JSONResponse(
      operator.portfolio(
          current_user, portfolio_uri
      ).facility(facility_uri).device_manager.link_to_component(device_uri, component_uri)
    )
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to link device to component: {e}"},
        status_code=500
    )

@app.get("/device/graphic", tags=['Devices'])
async def get_device_graphic(
  portfolio_uri: str,
  facility_uri: str,
  device_uri: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    return Response(
      operator.portfolio(
          current_user, portfolio_uri
      ).facility(facility_uri).device(device_uri).graphic(), 
      media_type="image/svg+xml"
    )
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to get device graphic: {e}"},
        status_code=500
    )
  
### POINTS ROUTES
@app.get("/points", tags=['Points'])
async def list_points(
  portfolio_uri: str,
  facility_uri: str,
  device_uri: str | None = None,
  component_uri: str | None = None,
  collect_enabled: bool | None = None,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  points = operator.portfolio(current_user, portfolio_uri).facility(facility_uri).point_manager.points(device_uri, collect_enabled, component_uri)
  for point in points: # Remove the embedding from the response
    point.pop('embedding', None)
  return JSONResponse(points)

@app.get("/points/history", tags=['Points'])
async def get_points_history(
  portfolio_uri: str,
  facility_uri: str,
  start_time: str,
  end_time: str,
  device_uri: str | None = None,
  component_uri: str | None = None,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  return JSONResponse(
    operator.portfolio(current_user, portfolio_uri).facility(facility_uri).point_manager.points_history(start_time, end_time, device_uri, component_uri)
  )

## BACNET INTEGRATION ROUTES
@app.post("/bacnet/import", tags=['BACnet'])
async def upload_bacnet_data(
  portfolio_uri: str,
  facility_uri: str,
  file: UploadFile,
  vectorize: bool = False,
  current_user: User = Security(get_current_user)
):
  try:
    file_content = await file.read()
    operator.portfolio(
      current_user,
      portfolio_uri
    ).facility(facility_uri).bacnet.upload_bacnet_data(file_content)

    if vectorize:
      operator.portfolio(
        current_user,
        portfolio_uri
      ).facility(facility_uri).device_manager.vectorize()

      operator.portfolio(
        current_user,
        portfolio_uri
      ).facility(facility_uri).point_manager.vectorize_graph()

    return "BACnet data uploaded successfully"
  except HTTPException as e:
    return Response(content=str(e), status_code=500)

## TIMESERIES
@app.get("/timeseries", tags=['Timeseries'], response_model=List[TimeseriesReading])
async def get_timeseries_data(
  timeseriesIds: List[str] = Query(...),
  start_time: str = Query(...),
  end_time: str = Query(...),
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    data = operator.timescale.get_timeseries(timeseriesIds, start_time, end_time)
    # data = [reading.model_dump() for reading in data]
    return JSONResponse(data)
  except HTTPException as e:
    return JSONResponse(
        content={"message": f"Unable to get timeseries: {e}"},
        status_code=500
    )
  
if __name__ == "__main__":
  reload = True if os.environ.get("ENV") == "dev" else False
  uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=reload)