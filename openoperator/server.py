from .schema.message import Message
from .user import User 

import mimetypes

from typing import Generator
from fastapi import FastAPI, UploadFile, Depends, Security, HTTPException
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

def server(operator, host="0.0.0.0", port=8080):
    app = FastAPI(title="Open Operator API")

    security = HTTPBearer()

    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        token = credentials.credentials
        try:
            user = operator.get_user_from_access_token(token)
            return user
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
    

    @app.post("/signup", tags=["Auth"])
    async def signup(email: str, password: str, full_name: str) -> JSONResponse:
        try:
            return JSONResponse(operator.user(email, password, full_name).signup())
        except Exception as e:
            return JSONResponse(content={"message": f"Unable to create user: {e}"}, status_code=500)
        
    @app.post("/login", tags=["Auth"])
    async def login(email: str, password: str) -> JSONResponse:
        try:
            return JSONResponse(operator.user(email, password, "").login()) 
        except Exception as e:
            return JSONResponse(content={"message": f"Unable to login: {e}"}, status_code=500)
        

    @app.post("/chat", tags=["Assistant"])
    async def chat(messages: list[Message], portfolio_uri: str, facility_uri: str | None = None, current_user: User = Security(get_current_user)) -> StreamingResponse:
        messages_dict_list = [message.model_dump() for message in messages]

        portfolio = operator.portfolio(current_user, portfolio_uri)
        facility = None
        if facility_uri:
            facility = portfolio.facility(facility_uri)

        async def event_stream() -> Generator[str, None, None]:
            for response in operator.chat(messages=messages_dict_list, portfolio=portfolio, facility=facility):
                yield response
        
        return StreamingResponse(event_stream(), media_type="text/event-stream")

        
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
    async def create_portfolio(portfolio_name: str, current_user: User = Security(get_current_user)) -> JSONResponse:
        portfolio = operator.create_portfolio(current_user, portfolio_name)
        return JSONResponse(portfolio.details())

    @app.get("/portfolio/facilities", tags=['Portfolio'])
    async def list_facilities(portfolio_uri: str, current_user: User = Security(get_current_user)) -> JSONResponse:
        try:
            return JSONResponse(operator.portfolio(current_user, portfolio_uri).list_facilities())
        except Exception as e:
            return Response(content="Unable to create portfolio", status_code=500)

    @app.post("/portfolio/facility/create", tags=['Facility'])
    async def create_facility(portfolio_uri: str, building_name: str, current_user: User = Security(get_current_user)) -> JSONResponse:
        return JSONResponse(operator.portfolio(current_user, portfolio_uri).create_facility(building_name).details())
    

    @app.get("/portfolio/facility/documents", tags=['Facility'])
    async def list_documents(portfolio_uri: str, facility_uri: str, current_user: User = Security(get_current_user)) -> JSONResponse:
        return JSONResponse(operator.portfolio(current_user, portfolio_uri).facility(facility_uri).documents())
    
    @app.delete("/portfolio/facility/document/delete", tags=['Facility'])
    async def delete_document(portfolio_uri: str, facility_uri: str, document_url: str, current_user: User = Security(get_current_user)) -> Response:
        try:
            operator.portfolio(current_user, portfolio_uri).facility(facility_uri).delete_document(document_url)
            return JSONResponse(content={
                "message": "Document deleted successfully",
            })
        except Exception as e:
            return Response(content=str(e), status_code=500)
        

    @app.post("/portfolio/facility/documents/upload", tags=['Facility'])
    async def upload_file(file: UploadFile, portfolio_uri: str, facility_uri: str | None = None, current_user: User = Security(get_current_user)):
        try:
            file_content = await file.read()
            file_type = mimetypes.guess_type(file.filename)[0]
            operator.portfolio(current_user, portfolio_uri).facility(facility_uri).upload_document(file_content=file_content, file_name=file.filename, file_type=file_type)
            return "File uploaded successfully"
        except Exception as e:
            print(e)
            return Response(content=str(e), status_code=500) 
        


    ## BAS INTEGRATION ROUTES
    @app.post("/bas/upload_json_scan", tags=['BAS'])
    async def upload_bacnet(portfolio_uri: str, facility_uri: str, file: UploadFile, current_user: User = Security(get_current_user)):
        try:
            file_content = await file.read()
            operator.portfolio(current_user, portfolio_uri).facility(facility_uri).bas.upload_bacnet_data(file_content)
            return "BACnet data uploaded successfully"
        except Exception as e:
            return Response(content=str(e), status_code=500)
        
    @app.get("/bas/devices", tags=['BAS'])
    async def list_devices(portfolio_uri: str, facility_uri: str, current_user: User = Security(get_current_user)) -> JSONResponse:
        return JSONResponse(operator.portfolio(current_user, portfolio_uri).facility(facility_uri).bas.devices())
    
    @app.get("/bas/points", tags=['BAS'])
    async def list_points(portfolio_uri: str, facility_uri: str, device_uri: str | None = None, current_user: User = Security(get_current_user)) -> JSONResponse:
        if device_uri is None:
            return JSONResponse(operator.portfolio(current_user, portfolio_uri).facility(facility_uri).bas.points())
        return JSONResponse(operator.portfolio(current_user, portfolio_uri).facility(facility_uri).bas.points(device_uri))
        
    
    

    print("\nServer is running. Visit http://localhost:8080/docs to see documentation\n")

    uvicorn.run(app, host=host, port=port)