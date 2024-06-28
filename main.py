import os
from fastapi import FastAPI, APIRouter
from fastapi_sqlalchemy import DBSessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.core.main_router import router as main_router
from app.user import user_router
from app.Client import client_router
from app.Membership import membership_router
from app.Coach import coach_router
from app.Event import event_router
from app.Leads import leads_router
# import logging

load_dotenv(".env")

root_router = APIRouter()

app = FastAPI(title="Lets Move API")

app.add_middleware(CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(main_router)
app.include_router(user_router)
app.include_router(client_router)
app.include_router(coach_router)
app.include_router(membership_router)
app.include_router(event_router)
app.include_router(leads_router)
app.include_router(root_router)

AUTH_BASE_URL = os.environ.get("AUTH_BASE_URL")
# logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":

    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)