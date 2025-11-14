import os
import time
from typing import Annotated
from fastapi import (
    Depends,
    FastAPI,
    APIRouter,
    HTTPException,
    Header,
    Request,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from fastapi_sqlalchemy import DBSessionMiddleware
import jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from starlette.status import HTTP_401_UNAUTHORIZED
from app.core.main_router import router as main_router
from app.user import user_router

load_dotenv(".env")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRY = os.getenv("JWT_EXPIRY", "")
ROOT_PATH = "/fastapi"

bearer_scheme = HTTPBearer()


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
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        raise token_expection
    if (time.time() - payload["token_time"]) > int(JWT_EXPIRY):
        raise token_expection
    request.state.user = payload


root_router = APIRouter(dependencies=[Depends(authorization)])

app = FastAPI(title="Lets Move API", root_path=ROOT_PATH, swagger_ui_parameters={'displayRequestDuration': True})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(main_router)
root_router.include_router(user_router)
app.include_router(root_router)

AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL")
# logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":

    import uvicorn

    uvicorn.run("main:app", port=8000, reload=True)
