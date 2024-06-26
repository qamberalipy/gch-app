from datetime import date
import jwt
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Business.schema as _schemas
import app.Business.models as _models
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


def create_business(business: _schemas.BusinessCreate, db: _orm.Session):
    db_business = models.Business(
        name=business.name,
        address=business.address,
        email=business.email,
        owner_id=business.owner_id,
        org_id=business.org_id,
        date_created=date.today()
    )
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return db_business

def get_businesses_by_org_id(org_id: int, db: _orm.Session):
    return db.query(models.Business).filter(
        models.Business.org_id == org_id,
        models.Business.is_deleted == False
    ).all()
    
    