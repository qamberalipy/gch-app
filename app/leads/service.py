from datetime import date
import jwt
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Leads.schema as _schemas
import app.Leads.models as _models
import random
import json
import pika
import time
import os
import bcrypt as _bcrypt
from . import models, schema

# Load environment variables
# JWT_SECRET = os.getenv("JWT_SECRET")
# oauth2schema = _security.OAuth2PasswordBearer("/token")


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

async def create_lead(client: _schemas.LeadCreate, db: _orm.Session = _fastapi.Depends(get_db)):
    db_lead = _models.Leads(**client.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead





