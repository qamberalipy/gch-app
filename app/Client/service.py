from datetime import date
import jwt
from sqlalchemy import func
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Client.schema as _schemas
import app.Client.models as _models
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
        
        
async def create_client(client: _schemas.RegisterClient, db: _orm.Session = _fastapi.Depends(get_db)):
    db_client = _models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

async def create_client_organization(client_organization: _schemas.CreateClientOrganization, db: _orm.Session = _fastapi.Depends(get_db)):
    db_client_organization = _models.ClientOrganization(**client_organization.dict())
    db.add(db_client_organization)
    db.commit()
    db.refresh(db_client_organization)
    return db_client_organization

async def create_client_membership(client_membership: _schemas.CreateClientMembership, db: _orm.Session = _fastapi.Depends(get_db)):
    db_client_membership = _models.ClientMembership(**client_membership.dict())
    db.add(db_client_membership)
    db.commit()
    db.refresh(db_client_membership)
    return db_client_membership

async def create_client_coach(client_coach: _schemas.CreateClientCoach, db: _orm.Session = _fastapi.Depends(get_db)):
    db_client_coach = _models.ClientCoach(**client_coach.dict())
    db.add(db_client_coach)
    db.commit()
    db.refresh(db_client_coach)
    return db_client_coach

async def authenticate_client(email_address: str, db: _orm.Session = _fastapi.Depends(get_db)):
    client = get_client_by_email(email_address , db)
      
    if not client:
        return False
   
    return client

async def login_client(email_address: str, wallet_address: str, db: _orm.Session = _fastapi.Depends(get_db)) -> dict:
    client = get_client_by_email(email_address, db)
    
    if not client:
        return {"is_registered": False}
    
    client.wallet_address = wallet_address
    db.commit()
    db.refresh(client)
    return {"is_registered": True}

def get_client_by_email(email_address: str, db: _orm.Session = _fastapi.Depends(get_db)) -> models.Client:
    return db.query(models.Client).filter(models.Client.email == email_address).first()
    
async def get_business_clients(org_id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    clients = db.query(
        models.Client.id,
        models.Client.first_name
    ).join(
        models.ClientOrganization,
        models.ClientOrganization.client_id == models.Client.id
    ).filter(
        models.ClientOrganization.org_id == org_id,
        models.Client.is_business == True
    ).all()

    return clients


async def get_total_clients(org_id: int, db: _orm.Session = _fastapi.Depends(get_db)) -> int:
    total_clients = db.query(func.count(models.Client.id)).join(
        models.ClientOrganization,
        models.ClientOrganization.client_id == models.Client.id
    ).filter(
        models.ClientOrganization.org_id == org_id
    ).scalar()
    
    return total_clients