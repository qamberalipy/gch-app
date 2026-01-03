# app/user/service.py
from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status
import sqlalchemy.orm as _orm
from sqlalchemy import or_

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
    
    # Exclude unset fields so we don't overwrite with None
    update_data = user_in.dict(exclude_unset=True)

    if "email" in update_data:
        new_email = update_data["email"]
        if new_email != user.email: # Only check if it's actually changing
            if check_email_exists(db, new_email):
                raise HTTPException(status_code=400, detail="Email already currently in use")
    
    # 2. Check Username Duplication
    if "username" in update_data:
        new_username = update_data["username"]
        if new_username != user.username:
            if not check_username_available(db, new_username):
                raise HTTPException(status_code=400, detail="Username already taken")

    # --- HANDLE PASSWORD HASHING ---
    print("Update Data Before Password Handling:", update_data)
    if "password" in update_data:
        password = update_data.pop("password") # Remove from dict so we don't save plain text
        if password: # If not empty string
            user.set_password(password)

    # --- UPDATE FIELDS ---
    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    user.updated_at = datetime.utcnow()
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        # Catch unexpected DB errors (like string length too long)
        raise HTTPException(status_code=500, detail=str(e))

def soft_delete_user(db: _orm.Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create a unique suffix
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    
    # Mask Email & Username to free them up
    # e.g. "john@gmail.com" -> "john@gmail.com_del_20260103"
    user.email = f"{user.email}_del_{timestamp}"
    if user.username:
        user.username = f"{user.username}_del_{timestamp}"

    user.is_deleted = True
    user.account_status = _models.AccountStatus.deleted
    
    db.add(user)
    db.commit()
    return True

def get_all_users_filtered(
    db: _orm.Session, 
    current_user_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    role: _models.UserRole = None, 
    search: str = None
):
    
    query = db.query(_models.User).filter(
        _models.User.is_deleted == False,
        _models.User.id != current_user_id
    )

    if role:
        query = query.filter(_models.User.role == role)

    if search and search.strip():
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                _models.User.full_name.ilike(search_fmt),
                _models.User.username.ilike(search_fmt),
                _models.User.email.ilike(search_fmt)
            )
        )

    return query.offset(skip).limit(limit).all()

def change_user_password(db: _orm.Session, user_id: int, password_data: _schemas.ChangePassword):
    # 1. Get the user
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Verify Old Password (Security Check)
    if not user.verify_password(password_data.old_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # 3. Hash and Save New Password
    user.set_password(password_data.new_password)
    user.updated_at = datetime.utcnow()
    
    db.add(user)
    db.commit()
    
    return {"message": "Password updated successfully"}