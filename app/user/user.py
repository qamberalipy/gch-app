# app/user/user.py
from typing import List,Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

import app.user.schema as _schemas
import app.user.service as _services
import app.user.models as _models

router = APIRouter()

# --- Dependency Injection ---

def get_db():
    # Use the generator from service to ensure consistency
    return _services.get_db()

async def get_current_user(request: Request,db: Session = Depends(_services.get_db)) -> _models.User:
   
    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(status_code=401, detail="Authentication credentials missing")
    
    payload = request.state.user
    
    sub = payload.get("sub")
    user_id = None
    
    if isinstance(sub, dict):
        user_id = sub.get("user_id")
    elif isinstance(sub, (str, int)):
        user_id = sub
        
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = _services.get_user_by_id(db, user_id=int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user

async def get_admin_or_manager(current_user: _models.User = Depends(get_current_user)) -> _models.User:
    if current_user.role not in [_models.UserRole.admin, _models.UserRole.manager]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user


@router.post("/", response_model=_schemas.UserOut, status_code=status.HTTP_201_CREATED,tags=["User CURD API"])
async def create_user(
    user_in: _schemas.UserCreate,
    current_user: _models.User = Depends(get_admin_or_manager),
    db: Session = Depends(_services.get_db)
):
    # Manager restriction logic
    if current_user.role == _models.UserRole.manager and user_in.role == _schemas.UserRoleEnum.admin:
        raise HTTPException(status_code=403, detail="Managers cannot create Admins")
        
    return _services.create_user_by_admin(db, user_in)

@router.put("/{user_id}", response_model=_schemas.UserOut, tags=["User CURD API"])
async def update_user(
    user_id: int,
    user_in: _schemas.UserUpdate,
    current_user: _models.User = Depends(get_current_user),
    db: Session = Depends(_services.get_db)
):
    # Logic: Can update self, OR must be admin/manager
    is_privileged = current_user.role in [_models.UserRole.admin, _models.UserRole.manager]
    
    if current_user.id != user_id and not is_privileged:
        raise HTTPException(status_code=403, detail="Cannot update other users")

    return _services.update_user_details(db, user_id, user_in)

@router.delete("/{user_id}", tags=["User CURD API"])
async def delete_user(
    user_id: int,
    current_user: _models.User = Depends(get_admin_or_manager),
    db: Session = Depends(_services.get_db)
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
    _services.soft_delete_user(db, user_id)
    return {"message": "User deleted"}


@router.get("/", response_model=List[_schemas.UserOut], tags=["User CURD API"])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[_models.UserRole] = None, # Filter by specific role
    search: Optional[str] = None,            # Search by name/email/username
    current_user: _models.User = Depends(get_admin_or_manager),
    db: Session = Depends(_services.get_db)
):
    return _services.get_all_users_filtered(
        db=db, 
        current_user_id=current_user.id, 
        skip=skip, 
        limit=limit, 
        role=role, 
        search=search
    )

@router.get("/{user_id}", response_model=_schemas.UserOut, tags=["User CURD API"])
async def get_user_by_id(
    user_id: int,
    current_user: _models.User = Depends(get_current_user),
    db: Session = Depends(_services.get_db)
):
    user = _services.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user