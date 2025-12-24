# app/user/service.py
from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status
import sqlalchemy.orm as _orm

import app.user.models as _models
import app.user.schema as _schemas
import app.core.db.session as _database

# --- DB Dependency ---
def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helpers ---
def check_email_exists(db: _orm.Session, email: str) -> bool:
    return db.query(_models.User).filter(
        _models.User.email == email, 
        _models.User.is_deleted == False
    ).first() is not None

def check_username_available(db: _orm.Session, username: str) -> bool:
    return db.query(_models.User).filter(
        _models.User.username == username, 
        _models.User.is_deleted == False
    ).first() is None

def get_user_by_id(db: _orm.Session, user_id: int) -> Optional[_models.User]:
    return db.query(_models.User).filter(
        _models.User.id == user_id, 
        _models.User.is_deleted == False
    ).first()

# --- CRUD Operations ---

def create_user_by_admin(db: _orm.Session, user_in: _schemas.UserCreate) -> _models.User:
    """Creates a user with hashed password"""
    
    # 1. Validate Uniqueness
    if check_email_exists(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if not check_username_available(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    # 2. Map Schema to Model
    db_user = _models.User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        role=user_in.role,
        phone=user_in.phone,
        bio=user_in.bio,
        country_id=user_in.country_id,
        city=user_in.city,
        address_1=user_in.address_1,
        gender=user_in.gender,
        is_onboarded=True,
        created_at=datetime.utcnow()
    )
    
    # 3. Hash Password (using method inside Model)
    db_user.set_password(user_in.password)
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def update_user_details(db: _orm.Session, user_id: int, user_in: _schemas.UserUpdate) -> _models.User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only update fields that are provided
    update_data = user_in.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    user.updated_at = datetime.utcnow()
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def soft_delete_user(db: _orm.Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_deleted = True
    user.account_status = _models.AccountStatus.deleted
    
    db.add(user)
    db.commit()
    return True

def get_all_users_filtered(db: _orm.Session, current_user_id: int, skip: int = 0, limit: int = 100):
    return db.query(_models.User).filter(
        _models.User.is_deleted == False,
        _models.User.id != current_user_id  # Exclude self
    ).offset(skip).limit(limit).all()