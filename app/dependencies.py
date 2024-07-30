
from typing import Annotated
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from .core.db import session as _database
from .Client import service as _client_service

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_user(request: Request, db: Annotated[Session, Depends(get_db)]):
    return await _client_service.get_client_by_email(request.state.user['email'], db)
