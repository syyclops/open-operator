from .schema.message import Message

import mimetypes

from typing import Generator
from fastapi import FastAPI, UploadFile, Depends, Security, HTTPException
from fastapi.requests import Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

import jwt
import os   


class User(BaseModel):
    email: str

def server(operator, host="0.0.0.0", port=8080):
    app = FastAPI(title="Open Operator API")

    security = HTTPBearer()

    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        token = credentials.credentials
        secret_key = os.environ.get("API_TOKEN_SECRET") 
        decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
        email = decoded_token["email"]

        with operator.neo4j_driver.session() as session:
            result = session.run("MATCH (u:User {email: $email}) RETURN u", email=email)
            user = result.single()
            if user is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            user_data = user['u']

        return User(email=user_data['email'])


    @app.post("/chat", tags=["assistant"])
    async def chat(messages: list[Message], portfolio_uri: str, facility_uri: str | None = None) -> StreamingResponse:
        messages_dict_list = [message.model_dump() for message in messages]

        portfolio = operator.portfolio(portfolio_uri)
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


    @app.get("/portfolio/list", tags=['portfolio'])
    async def list_portfolios(current_user: str = Security(get_current_user)) -> JSONResponse:
        print(current_user.email)
        return JSONResponse(operator.portfolios())

    @app.post("/portfolio/create", tags=['portfolio'])
    async def create_portfolio(portfolio_name: str) -> JSONResponse:
        portfolio = operator.create_portfolio(portfolio_name)
        return JSONResponse(portfolio.details())

    @app.get("/portfolio/facilities", tags=['portfolio'])
    async def list_facilities(portfolio_uri: str) -> JSONResponse:
        try:
            return JSONResponse(operator.portfolio(portfolio_uri).list_facilities())
        except Exception as e:
            return Response(content="Unable to create portfolio", status_code=500)

    @app.post("/portfolio/facility/create", tags=['facility'])
    async def create_facility(portfolio_uri: str, building_name: str) -> JSONResponse:
        return JSONResponse(operator.portfolio(portfolio_uri).create_facility(building_name).details())
    

    @app.get("/portfolio/facility/documents", tags=['facility'])
    async def list_documents(portfolio_uri: str, facility_uri: str) -> JSONResponse:
        return JSONResponse(operator.portfolio(portfolio_uri).facility(facility_uri).documents())
    
    @app.delete("/portfolio/facility/document/delete", tags=['facility'])
    async def delete_document(portfolio_uri: str, facility_uri: str, document_url: str) -> Response:
        try:
            operator.portfolio(portfolio_uri).facility(facility_uri).delete_document(document_url)
            return JSONResponse(content={
                "message": "Document deleted successfully",
            })
        except Exception as e:
            return Response(content=str(e), status_code=500)
        

    @app.post("/portfolio/facility/documents/upload", tags=['facility'])
    async def upload_file(file: UploadFile, portfolio_uri: str, facility_uri: str | None = None):
        try:
            file_content = await file.read()
            file_type = mimetypes.guess_type(file.filename)[0]
            operator.portfolio(portfolio_uri).facility(facility_uri).upload_document(file_content=file_content, file_name=file.filename, file_type=file_type)
            return "File uploaded successfully"
        except Exception as e:
            print(e)
            return Response(content=str(e), status_code=500) 
        
    

    print("\nServer is running. Visit http://localhost:8080/docs to see documentation\n")

    uvicorn.run(app, host=host, port=port)