# app/user/service.py
from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status
import sqlalchemy.orm as _orm
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

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

def get_available_users(db: _orm.Session, role: str) -> List[_models.User]:
    """Returns users of a specific role who are not assigned to anyone yet."""
    return db.query(_models.User).filter(
        _models.User.role == role,
        _models.User.assigned_model_id == None,
        _models.User.is_deleted == False
    ).all()

# --- CRUD Operations ---

def create_user(db: _orm.Session, user_in: _schemas.UserCreate, creator: _models.User) -> _models.User:
    # 1. Pre-checks
    if check_email_exists(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    if not check_username_available(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    try:
        # Exclude special fields to handle manually
        user_data = user_in.dict(exclude={"password", "manager_id", "assigned_model_id"})
        db_user = _models.User(**user_data, created_at=datetime.utcnow(), is_onboarded=True)
        db_user.set_password(user_in.password)

        # 2. Manager Assignment Logic
        if creator.role == _models.UserRole.manager:
            db_user.manager_id = creator.id
        elif user_in.manager_id:
            db_user.manager_id = user_in.manager_id

        db.add(db_user)
        db.flush() # Flush to get ID, but don't commit yet

        # 3. Model <-> Team Member Assignment (1:1 Exclusive)
        if user_in.assigned_model_id and user_in.role in [_models.UserRole.team_member, _models.UserRole.digital_creator]:
            target = get_user_by_id(db, user_in.assigned_model_id)
            if target:
                if target.assigned_model_id:
                    raise HTTPException(status_code=400, detail="Selected user is already assigned to someone else.")
                
                db_user.assigned_model_id = target.id
                target.assigned_model_id = db_user.id

        db.commit()
        db.refresh(db_user)
        return db_user

    except IntegrityError as e:
        db.rollback()
        print(f"Database Integrity Error: {e}")
        raise HTTPException(status_code=400, detail="User creation failed due to database constraint.")
    except Exception as e:
        db.rollback()
        print(f"Unexpected Error in create_user: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during user creation.")

def update_user(db: _orm.Session, user_id: int, user_in: _schemas.UserUpdate, current_user: _models.User) -> _models.User:
    user = get_user_by_id(db, user_id)
    if not user: 
        raise HTTPException(status_code=404, detail="User not found")

    try:
        update_data = user_in.dict(exclude_unset=True)

        # --- HIERARCHY UPDATES (Admin/Manager Only) ---
        if current_user.role in [_models.UserRole.admin, _models.UserRole.manager]:
            
            # Manager Change
            if "manager_id" in update_data:
                user.manager_id = update_data.pop("manager_id")
            
            # Assignment Change (Swap Logic)
            if "assigned_model_id" in update_data:
                new_target_id = update_data.pop("assigned_model_id")
                
                # Unlink current assignment if exists
                if user.assigned_model_id:
                    old_target = get_user_by_id(db, user.assigned_model_id)
                    if old_target: 
                        old_target.assigned_model_id = None
                
                # Link new assignment if provided
                if new_target_id:
                    new_target = get_user_by_id(db, new_target_id)
                    if new_target:
                        # Steal/Overwrite logic
                        if new_target.assigned_model_id:
                            previous_owner = get_user_by_id(db, new_target.assigned_model_id)
                            if previous_owner:
                                previous_owner.assigned_model_id = None
                        
                        user.assigned_model_id = new_target.id
                        new_target.assigned_model_id = user.id
                    else:
                        user.assigned_model_id = None
                else:
                    user.assigned_model_id = None

        # --- GENERAL PROFILE UPDATES ---
        if "password" in update_data:
            user.set_password(update_data.pop("password"))
        
        # Cleanup
        update_data.pop("role", None) 
        
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update failed. Username or Email may already exist.")
    except Exception as e:
        db.rollback()
        print(f"Update Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

def soft_delete_user(db: _orm.Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        user.email = f"{user.email}_del_{timestamp}"
        if user.username:
            user.username = f"{user.username}_del_{timestamp}"
        
        # Unlink relationships
        if user.assigned_model_id:
            partner = get_user_by_id(db, user.assigned_model_id)
            if partner:
                partner.assigned_model_id = None
            user.assigned_model_id = None

        user.is_deleted = True
        user.account_status = _models.AccountStatus.deleted
        
        db.add(user)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

def get_all_users(db: _orm.Session, current_user: _models.User, role=None, search=None, skip=0, limit=100):
    query = db.query(_models.User).filter(_models.User.is_deleted == False)
    
    if current_user.role == _models.UserRole.manager:
        query = query.filter(_models.User.manager_id == current_user.id)
    
    if role: 
        query = query.filter(_models.User.role == role)
    
    if search:
        s = f"%{search}%"
        query = query.filter(or_(_models.User.full_name.ilike(s), _models.User.email.ilike(s)))

    return query.offset(skip).limit(limit).all()

def change_user_password(db: _orm.Session, user_id: int, password_data: _schemas.ChangePassword):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.verify_password(password_data.old_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    try:
        user.set_password(password_data.new_password)
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        return {"message": "Password updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update password")