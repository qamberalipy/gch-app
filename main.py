import os
import time
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi_sqlalchemy import DBSessionMiddleware
import jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.core.main_router import router as main_router
from app.user import user_router
from app.Client import client_router
from app.MealPlan import mealplan_router
from app.Membership import membership_router
from app.Coach import coach_router
from app.Event import event_router
from app.Exercise import exercise_router
from app.Leads import leads_router
from app.Food import food_router
from app.Shared.helpers import verify_jwt

load_dotenv(".env")
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_EXPIRY = os.getenv("JWT_EXPIRY", "")

root_router = APIRouter()

app = FastAPI(
    title="Lets Move API",
    root_path="/fastapi"
)

app.add_middleware(CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.middleware("http")
async def jwt_niddleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
    myroutes = ("/workout")
    if not request.url.path.startswith(myroutes):
        response = await call_next(request)
        return response

    authorization = request.headers.get('Authorization') 

    if not authorization or not authorization.startswith("Bearer"):
        return JSONResponse(status_code=401, content={"detail":"Invalid or missing access token"})

    token = authorization.split("Bearer ")[1]
    token_expection = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail":"Token Expired or Invalid"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        return token_expection
    
    print("Token time: ", (time.time() - payload["token_time"]) > int(JWT_EXPIRY), time.time() - payload["token_time"], int(JWT_EXPIRY))
    if (time.time() - payload["token_time"]) > int(JWT_EXPIRY):
        return token_expection
    if payload['user_type'] != "user":
        return token_expection

    request.state.user = payload
    response = await call_next(request)
    return response

app.include_router(main_router)
app.include_router(user_router)
app.include_router(client_router)
app.include_router(coach_router)
app.include_router(membership_router)
app.include_router(event_router)
app.include_router(leads_router)
app.include_router(mealplan_router)
app.include_router(food_router)
app.include_router(root_router)
app.include_router(exercise_router)

AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL")
# logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":

    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
