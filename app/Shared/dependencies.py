from typing import Annotated, Literal
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.user.models import Permission, Resource, Role

from .schema import PaginationOptions

from ..core.db import session as _database
from ..Client import service as _client_service


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_user(request: Request):  # , db: Annotated[Session, Depends(get_db)]):
    return request.state.user


# return await _client_service.get_client_by_email(request.state.user['email'], db)


def get_pagination_options(
    _limit: Annotated[
        int | None,
        Query(title="Limit", description="Number of results in response"),
    ] = None,
    _offset: Annotated[
        int | None, Query(description="How many results to skip")
    ] = None,
):
    return PaginationOptions(limit=_limit, offset=_offset)


def get_module_permission(module: str, request_type: Literal["read","write","delete"]):
    def get_permission(request: Request, db: Annotated[Session, Depends(get_db)]):
        user = request.state.user
        if user["user_type"] != "staff":
            return
        access_type = (
            db.query(Permission.access_type)
            .join(Resource, Resource.id == Permission.resource_id)
            .filter(Resource.name == module, Permission.role_id == user["role_id"])
            .scalar()
        )
        if access_type == "full_access":
            return
        if request_type == "delete":
            raise HTTPException(status_code=403, detail="You don't have access")
        if access_type == "no_access":
            raise HTTPException(status_code=403, detail="You don't have access")
        if access_type == "read" and request_type == "write":
            raise HTTPException(status_code=403, detail="You don't have access")

    return get_permission
