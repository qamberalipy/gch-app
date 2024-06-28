from datetime import date
from typing import List
import jwt
from sqlalchemy import func, or_
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

async def get_client_by_email(email_address: str, db: _orm.Session = _fastapi.Depends(get_db)) -> models.Client:
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

async def get_filtered_clients(params: _schemas.ClientFilterParams,db: _orm.Session = _fastapi.Depends(get_db)) -> List[_schemas.ClientFilterRead]:
    query = db.query(_models.Client)\
        .join(_models.ClientOrganization, _models.Client.id == _models.ClientOrganization.client_id)\
        .join(_models.ClientCoach, _models.Client.id == _models.ClientCoach.client_id)\
        .join(_models.ClientMembership, _models.Client.id == _models.ClientMembership.client_id)\
        .filter(_models.ClientOrganization.org_id == params.org_id, _models.ClientOrganization.is_deleted == False)

    if params.client_name:
        query = query.filter(or_(
            _models.Client.first_name.ilike(f"%{params.client_name}%"),
            _models.Client.last_name.ilike(f"%{params.client_name}%")
        ))
    
    if params.status:
        query = query.filter(_models.ClientOrganization.client_status.ilike(f"%{params.status}%"))
    
    if params.coach_assigned:
        query = query.filter(_models.ClientCoach.coach_id == params.coach_assigned)
    
    if params.membership_plan:
        query = query.filter(_models.ClientMembership.membership_plan_id == params.membership_plan)
    
    if params.search_key:
        search_pattern = f"%{params.search_key}%"
        query = query.filter(or_(
            _models.Client.wallet_address.ilike(search_pattern),
            _models.Client.profile_img.ilike(search_pattern),
            _models.Client.own_member_id.ilike(search_pattern),
            _models.Client.first_name.ilike(search_pattern),
            _models.Client.last_name.ilike(search_pattern),
            _models.Client.gender.ilike(search_pattern),
            _models.Client.email.ilike(search_pattern),
            _models.Client.phone.ilike(search_pattern),
            _models.Client.mobile_number.ilike(search_pattern),
            _models.Client.notes.ilike(search_pattern),
            _models.Client.language.ilike(search_pattern),
            _models.Client.city.ilike(search_pattern),
            _models.Client.zipcode.ilike(search_pattern),
            _models.Client.address_1.ilike(search_pattern),
            _models.Client.address_2.ilike(search_pattern)
        ))

    clients = query.all()
    return clients