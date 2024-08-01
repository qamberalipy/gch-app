
from typing import Annotated
from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from .schema import PaginationOptions

from ..core.db import session as _database
from ..Client import service as _client_service

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_user(request: Request, db: Annotated[Session, Depends(get_db)]):
  return await _client_service.get_client_by_email(request.state.user['email'], db)

def get_pagination_options(
    _limit: Annotated[
        int | None,
        Query(title="Limit", description="Number of results in response"),
    ] = None,
    _offset: Annotated[
        int | None, 
        Query(description="How many results to skip")
    ] = None,
):
    return PaginationOptions(limit=_limit, offset=_offset)
