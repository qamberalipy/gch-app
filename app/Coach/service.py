from datetime import date
import jwt
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Coach.schema as _schemas
import app.Coach.models as _models
import random
import json
import pika
import time
import os
import bcrypt as _bcrypt
from . import models, schema

# Load environment variables
JWT_SECRET = os.getenv("JWT_SECRET")
oauth2schema = _security.OAuth2PasswordBearer("/token")


def create_database():
    # Create database tables
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    # Dependency to get a database session
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def create_coach(coach: _schemas.CoachCreate, db: _orm.Session):
    db_coach = models.Coach(coach_name=coach.coach_name)
    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)
    
    db_coach_org = models.CoachOrganization(coach_id=db_coach.id, org_id=coach.org_id)
    db.add(db_coach_org)
    db.commit()
    db.refresh(db_coach_org)
    
    return db_coach

def get_coaches_by_org_id(org_id: int, db: _orm.Session):
    return db.query(models.Coach).select_from(models.CoachOrganization).join(
        models.Coach, models.CoachOrganization.coach_id == models.Coach.id
    ).filter(
        and_(
            models.CoachOrganization.org_id == org_id,
            models.CoachOrganization.is_deleted == False,
            models.Coach.is_deleted == False
        )
    ).all()