import mimetypes
from typing import Generator
from fastapi import FastAPI, UploadFile, Depends, Security, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from io import BytesIO
from typing import List
from openoperator.types import DocumentQuery, Message
from openoperator.core.user import User

def server(operator, host="0.0.0.0", port=8080):
  """
  Start the Open Operator API server.
  """
  app = FastAPI(title="Open Operator API")
  security = HTTPBearer()

  async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
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

  @app.post("/chat", tags=["AI"], responses={
    200: {
      "content": {
        "plain/text": {
          "example": "{content: None}"
        }
      }
    }
  })
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
        yield str(response.model_dump())

    return StreamingResponse(event_stream(), media_type="text/event-stream")
    
  @app.post("/transcribe", tags=["AI"])
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

  @app.get("/portfolio/list", tags=['Portfolio'])
  async def list_portfolios(current_user: User = Security(get_current_user)) -> JSONResponse:
    return JSONResponse(operator.portfolios(current_user))

  @app.post("/portfolio/create", tags=['Portfolio'])
  async def create_portfolio(
    portfolio_name: str,
    current_user: User = Security(get_current_user)
  ) -> JSONResponse:
    portfolio = operator.create_portfolio(current_user, portfolio_name)
    return JSONResponse(portfolio.details())

  @app.get("/portfolio/facilities", tags=['Portfolio'])
  async def list_facilities(
    portfolio_uri: str,
    current_user: User = Security(get_current_user)
  ) -> JSONResponse:
    try:
      return JSONResponse(operator.portfolio(current_user, portfolio_uri).list_facilities())
    except HTTPException as e:
      return JSONResponse(
                  content={"message": f"Unable to list facilities: {e}"},
                  status_code=500
              )

  @app.post("/portfolio/facility/create", tags=['Facility'])
  async def create_facility(
    portfolio_uri: str,
    building_name: str,
    current_user: User = Security(get_current_user)
  ) -> JSONResponse:
    return JSONResponse(
      operator.portfolio(current_user, portfolio_uri).create_facility(building_name).details()
    )
    
  ## DOCUMENTS ROUTES

  @app.get("/portfolio/facility/documents", tags=['Documents'])
  async def list_documents(
    portfolio_uri: str,
    facility_uri: str,
    current_user: User = Security(get_current_user)
  ) -> JSONResponse:
    return JSONResponse(
      operator.portfolio(current_user, portfolio_uri).facility(facility_uri).documents.list()
    )
    
  @app.post("/portfolio/facility/documents/search", tags=['Documents'])
  async def search_documents(
    portfolio_uri: str,
    facility_uri: str,
    query: DocumentQuery,
    current_user: User = Security(get_current_user)
  ) -> JSONResponse:
    return JSONResponse(
      operator.portfolio(current_user, portfolio_uri).facility(facility_uri).documents.search(query.model_dump())
    )

  @app.delete("/portfolio/facility/document/delete", tags=['Documents'])
  async def delete_document(
    portfolio_uri: str,
    facility_uri: str,
    document_url: str,
    current_user: User = Security(get_current_user)
  ) -> Response:
    try:
      operator.portfolio(
        current_user,
        portfolio_uri
      ).facility(facility_uri).documents.delete(document_url)
      return JSONResponse(content={
        "message": "Document deleted successfully",
      })
    except HTTPException as e:
      return JSONResponse(
        content={"message": f"Unable to delete document: {e}"},
        status_code=500
      )

  @app.post("/portfolio/facility/documents/upload", tags=['Documents'])
  async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile],
    portfolio_uri: str,
    facility_uri: str,
    current_user: User = Security(get_current_user)
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

        file_url = document['url']
        background_tasks.add_task(operator.portfolio(
          current_user,
          portfolio_uri
        ).facility(facility_uri).documents.run_extraction_process, file_content, file.filename, file_url)

        uploaded_files_info.append({"filename": file.filename, "url": file_url})
      except Exception as e:  # Catching a more general exception; you might want to log this or handle it differently
        return JSONResponse(
            content={"message": f"Unable to upload file {file.filename}: {e}"},
            status_code=500
        )

    return {"message": "Files uploaded successfully", "uploaded_files": uploaded_files_info}

  ## BACNET INTEGRATION ROUTES
  @app.post("/portfolio/facility/bacnet/import", tags=['BACnet'])
  async def upload_bacnet_data(
    portfolio_uri: str,
    facility_uri: str,
    file: UploadFile,
    current_user: User = Security(get_current_user)
  ):
    try:
      file_content = await file.read()
      operator.portfolio(
        current_user,
        portfolio_uri
      ).facility(facility_uri).bacnet.upload_bacnet_data(file_content)

      operator.portfolio(
        current_user,
        portfolio_uri
      ).facility(facility_uri).bacnet.vectorize_graph()

      return "BACnet data uploaded successfully"
    except HTTPException as e:
      return Response(content=str(e), status_code=500)

  @app.get("/portfolio/facility/bacnet/devices", tags=['BACnet'])
  async def list_devices(
    portfolio_uri: str,
    facility_uri: str,
    current_user: User = Security(get_current_user)
  ) -> JSONResponse:
    try:
      return JSONResponse(
        operator.portfolio(
          current_user, portfolio_uri
        ).facility(facility_uri).bacnet.devices()
      )
    except HTTPException as e:
      return JSONResponse(
          content={"message": f"Unable to list devices: {e}"},
          status_code=500
      )
    
  @app.get("/portfolio/facility/bacnet/devices/cluster", tags=['BACnet'])
  async def list_device_cluster(
    portfolio_uri: str,
    facility_uri: str,
    current_user: User = Security(get_current_user)
  ) -> JSONResponse:
    return JSONResponse(
      operator.portfolio(
          current_user, portfolio_uri
      ).facility(facility_uri).bacnet.cluster_devices()
    )
  
  @app.get("/portfolio/facility/bacnet/device/link", tags=['BACnet'])
  async def link_bacnet_device(
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
        ).facility(facility_uri).bacnet.link_bacnet_device_to_cobie_component(device_uri, component_uri)
      )
    except HTTPException as e:
      return JSONResponse(
          content={"message": f"Unable to link device to component: {e}"},
          status_code=500
      )

  @app.get("/portfolio/facility/bacnet/points", tags=['BACnet'])
  async def list_points(
    portfolio_uri: str,
    facility_uri: str,
    device_uri: str | None = None,
    current_user: User = Security(get_current_user)
  ) -> JSONResponse:
    if device_uri is None:
      return JSONResponse(
        operator.portfolio(
            current_user, portfolio_uri
        ).facility(facility_uri).bacnet.points()
      )
    return JSONResponse(
      operator.portfolio(
          current_user, portfolio_uri
          ).facility(facility_uri).bacnet.points(device_uri)
      )
  
  @app.get("/portfolio/facility/bacnet/point/timeseries", tags=['BACnet'])
  async def get_timeseries(
    portfolio_uri: str,
    facility_uri: str,
    point_uri: str,
    start_time: str,
    end_time: str,
    current_user: User = Security(get_current_user)
  ) -> JSONResponse:
    print("Getting timeseries")
    print(point_uri)
    return JSONResponse(
      operator.portfolio(
          current_user, portfolio_uri
      ).facility(facility_uri).bacnet.timeseries(start_time, end_time, point_uri)
    )
  
  print("\nServer is running. Visit http://localhost:8080/docs to see documentation\n")
  uvicorn.run(app, host=host, port=port)