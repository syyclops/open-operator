from typing import List
from fastapi import FastAPI, Depends, Security, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import jwt
from openoperator.infastructure.knowledge_graph import KnowledgeGraph
from openoperator.domain.repository import PortfolioRepository, UserRepository
from openoperator.domain.service import PortfolioService, UserService
from openoperator.domain.model import Portfolio, User
from dotenv import load_dotenv
load_dotenv()

# Infrastructure
knowledge_graph = KnowledgeGraph()

# Repositories
portfolio_repository = PortfolioRepository(kg=knowledge_graph)
user_repository = UserRepository(kg=knowledge_graph)

# Services
base_uri = "https://syyclops.com/"
portfolio_service = PortfolioService(portfolio_repository=portfolio_repository, base_uri=base_uri)
user_service = UserService(user_repository=user_repository)

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

if __name__ == "__main__":
  reload = True if os.environ.get("ENV") == "dev" or os.environ.get("ENV") == "beta" else False
  uvicorn.run("openoperator.application.api.app:app", host="0.0.0.0", port=8080, reload=reload)