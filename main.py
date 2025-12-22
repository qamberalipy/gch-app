import os
import time
from typing import Annotated
from fastapi import (
    Depends,
    FastAPI,
    APIRouter,
    HTTPException,
    Request,
)
from fastapi.staticfiles import StaticFiles 
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from starlette.status import HTTP_401_UNAUTHORIZED
import jwt

# --- 0. LOAD ENV & VARIABLES FIRST ---
# (Move this to the top so the functions below can use them immediately)
load_dotenv(".env")

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRY = os.getenv("JWT_EXPIRY", "")
AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL")
ROOT_PATH = os.getenv("ROOT_PATH", "") 

# --- 1. IMPORT API ROUTERS ---
# These work because your folder 'app' is in the same directory as main.py
from app.core.main_router import router as main_router
from app.user import user_router

# --- 2. IMPORT WEB (HTML) ROUTERS ---
from app.web.routers import auth as web_auth

bearer_scheme = HTTPBearer()

# --- AUTH LOGIC (API ONLY) ---
async def authorization(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
):
    token = credentials.credentials
    token_expection = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Token Expired or Invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Now JWT_SECRET is definitely defined because we moved it up
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        raise token_expection
    
    # Ensure JWT_EXPIRY is treated as an integer
    if (time.time() - payload.get("token_time", 0)) > int(JWT_EXPIRY or 3600):
        raise token_expection
    request.state.user = payload

# Router for PROTECTED API endpoints
root_router = APIRouter(dependencies=[Depends(authorization)])

app = FastAPI(
    title="GCH App APIs", 
    root_path=ROOT_PATH, 
    swagger_ui_parameters={'displayRequestDuration': True}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --- 3. STATIC FILES SETUP ---
# This matches your image perfectly. 
# 'main.py' and 'static' folder are side-by-side in 'GCH-APP'.
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")

print(f"Mounting Static Files from: {static_dir}")

# Check if directory actually exists to prevent crash
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print("WARNING: static folder not found at", static_dir)

# --- 4. INCLUDE ALL ROUTERS ---
# Web Routes (HTML Pages)
app.include_router(web_auth.router)    


# API Routes
app.include_router(main_router)         
root_router.include_router(user_router) 
app.include_router(root_router)        

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    # Run the app
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)