import os
import time
from typing import Annotated
from fastapi import (
    Depends,
    FastAPI,
    APIRouter,
    HTTPException,
    Request,status
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
from app.upload import upload_router

# --- 2. IMPORT WEB (HTML) ROUTERS ---
from app.web.routers import auth_views
from app.web.routers import user_views

bearer_scheme = HTTPBearer()


async def authorization(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
):
    token = credentials.credentials
    
    # Define the exception to raise if validation fails
    token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token Expired or Invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        request.state.user = payload

    except jwt.ExpiredSignatureError:
        print("Token has expired.")
        raise token_exception
    except jwt.InvalidTokenError:
        print("Token is invalid.")
        raise token_exception
    except Exception as e:
        print(f"Token validation error: {e}")
        raise token_exception


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
app.include_router(auth_views.auth_view)    
app.include_router(user_views.user_view)
# API Routes
app.include_router(main_router)         
root_router.include_router(user_router) 
root_router.include_router(upload_router)
app.include_router(root_router)        

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    # Run the app
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)