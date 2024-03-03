from typing import List
import mimetypes
from fastapi import FastAPI, UploadFile, Depends, Security, HTTPException, BackgroundTasks
from fastapi.responses import Response, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import jwt
from openoperator.infastructure import KnowledgeGraph, AzureBlobStore, PGVectorStore, UnstructuredDocumentLoader, OpenAIEmbeddings, Postgres
from openoperator.domain.repository import PortfolioRepository, UserRepository, FacilityRepository, DocumentRepository
from openoperator.domain.service import PortfolioService, UserService, FacilityService, DocumentService
from openoperator.domain.model import Portfolio, User, Facility, Document, DocumentQuery, DocumentMetadataChunk
from dotenv import load_dotenv
load_dotenv()

# Infrastructure
knowledge_graph = KnowledgeGraph()
blob_store = AzureBlobStore()
document_loader = UnstructuredDocumentLoader()
embeddings = OpenAIEmbeddings()
postgres = Postgres()
vector_store = PGVectorStore(postgres=postgres, embeddings=embeddings)

# Repositories
portfolio_repository = PortfolioRepository(kg=knowledge_graph)
user_repository = UserRepository(kg=knowledge_graph)
facility_repository = FacilityRepository(kg=knowledge_graph)
document_repository = DocumentRepository(kg=knowledge_graph, blob_store=blob_store, document_loader=document_loader, vector_store=vector_store)

# Services
base_uri = "https://syyclops.com/"
portfolio_service = PortfolioService(portfolio_repository=portfolio_repository, base_uri=base_uri)
user_service = UserService(user_repository=user_repository)
facility_service = FacilityService(facility_repository=facility_repository)
document_service = DocumentService(document_repository=document_repository)

api_secret = os.getenv("API_SECRET")

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
    return User(email="example@example.com", hashed_password="", full_name="Example User")
  token = credentials.credentials
  try:
    decoded = jwt.decode(token, api_secret, algorithms=["HS256"])
    email = decoded.get("email")  
    user = user_service.get_user(email)
    return user
  except HTTPException as e:
    raise e
  
@app.post("/signup", tags=["Auth"])
async def signup(email: str, password: str, full_name: str) -> JSONResponse:
  try:
    user_service.create_user(email, full_name, password)
    token = jwt.encode({"email": email}, api_secret, algorithm="HS256")  
    return JSONResponse({
      "token": token,
    })
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to create user: {e}"}, status_code=500)

@app.post("/login", tags=["Auth"])
async def login(email: str, password: str) -> JSONResponse:
  try:
    verified = user_service.verify_user_password(email, password)
    if not verified:
      return JSONResponse(content={"message": "Invalid credentials"}, status_code=401)
    token = jwt.encode({"email": email}, api_secret, algorithm="HS256")
    return JSONResponse({"token": token})
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to login: {e}"}, status_code=500)

## PORTFOLIO ROUTES
@app.get("/portfolio/list", tags=['Portfolio'], response_model=List[Portfolio])
async def list_portfolios(current_user: User = Security(get_current_user)) -> JSONResponse:
  return JSONResponse([portfolio.model_dump() for portfolio in portfolio_service.list_portfolios_for_user(current_user.email)])

@app.post("/portfolio/create", tags=['Portfolio'], response_model=Portfolio)
async def create_portfolio(
  portfolio_name: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    portfolio = portfolio_service.create_portfolio(portfolio_name, current_user.email)
    return JSONResponse(portfolio.model_dump())
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to create portfolio: {e}"}, status_code=500)

## FACILITY ROUTES
@app.get("/facility/list", tags=['Facility'], response_model=List[Facility])
async def list_facilities(portfolio_uri: str, current_user: User = Security(get_current_user)) -> JSONResponse:
  return JSONResponse([facility.model_dump() for facility in facility_service.list_facilities_for_portfolio(portfolio_uri)])    

@app.post("/facility/create", tags=['Facility'], response_model=Facility)
async def create_facility(
  portfolio_uri: str,
  facility_name: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  try:
    facility = facility_service.create_facility(facility_name, portfolio_uri)
    return JSONResponse(facility.model_dump())
  except HTTPException as e:
    return JSONResponse(content={"message": f"Unable to create facility: {e}"}, status_code=500)

## DOCUMENTS ROUTES
@app.get("/documents", tags=['Document'], response_model=List[Document])
async def list_documents(
  portfolio_uri: str,
  facility_uri: str,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  docs = [doc.model_dump() for doc in document_service.list_documents(facility_uri)]
  return JSONResponse(docs)
  
@app.post("/documents/search", tags=['Document'], response_model=List[DocumentMetadataChunk])
async def search_documents(
  query: DocumentQuery,
  current_user: User = Security(get_current_user)
) -> JSONResponse:
  return JSONResponse([chunk.model_dump() for chunk in document_service.search(query)])

@app.post("/documents/upload", tags=['Document'])
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
      document = document_service.upload_document(facility_uri=facility_uri, file_content=file_content, file_name=file.filename, file_type=file_type)
      background_tasks.add_task(document_service.run_extraction_process, portfolio_uri, facility_uri, file_content, file.filename, document.uri, document.url)
      uploaded_files_info.append({"filename": file.filename, "uri": document.uri})
    except Exception as e:  # Catching a more general exception; you might want to log this or handle it differently
      return JSONResponse(
          content={"message": f"Unable to upload file {file.filename}: {e}"},
          status_code=500
      )

  return {"message": "Files uploaded successfully", "uploaded_files": uploaded_files_info}

@app.delete("/document/delete", tags=['Document'])
async def delete_document(
  portfolio_uri: str,
  facility_uri: str,
  document_uri: str,
  current_user: User = Security(get_current_user)
) -> Response:
  try:
    document_service.delete_document(document_uri)
    return JSONResponse(content={
      "message": "Document deleted successfully",
    })
  except HTTPException as e:
    return JSONResponse(
      content={"message": f"Unable to delete document: {e}"},
      status_code=400
    )
  
if __name__ == "__main__":
  reload = True if os.environ.get("ENV") == "dev" or os.environ.get("ENV") == "beta" else False
  uvicorn.run("openoperator.application.api.app:app", host="0.0.0.0", port=8080, reload=reload)