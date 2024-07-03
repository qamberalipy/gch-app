from datetime import date
import datetime
from typing import Optional

import jwt
from sqlalchemy import func, or_
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Leads.schema as _schemas
import app.Leads.models as _models
import app.user.models as _user_model
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

async def get_lead_by_id(id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(_models.Leads).filter(_models.Leads.id == id).first()

async def get_lead_by_email(email_address: str, db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(_models.Leads).filter(_models.Leads.email == email_address).first()

async def create_lead(lead: _schemas.LeadCreate, db: _orm.Session = _fastapi.Depends(get_db)):
    
    db_lead = _models.Leads(**lead.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

async def update_staff(data:_schemas.UpdateStatus, db: _orm.Session = _fastapi.Depends(get_db)):
    db_lead = db.query(_models.Leads).filter(_models.Leads.id == data.lead_id).first()
    if not db_lead:
        raise _fastapi.HTTPException(status_code=404, detail="lead not found")

    db_lead.staff_id=data.staff_id
    db.commit()
    db.refresh(db_lead)
    response={'lead_id':db_lead.id,'staff_id':db_lead.staff_id}
    return response


async def update_status(data:_schemas.UpdateStaff, db: _orm.Session = _fastapi.Depends(get_db)):
    db_lead = db.query(_models.Leads).filter(_models.Leads.id == data.lead_id).first()
    if not db_lead:
        raise _fastapi.HTTPException(status_code=404, detail="lead not found")

    db_lead.status=data.status
    db.commit()
    db.refresh(db_lead)
    response={'lead_id':db_lead.id,'status':db_lead.status}
    return response

async def update_data(lead_id:int,lead:_schemas.UpdateStaff, db: _orm.Session = _fastapi.Depends(get_db)):
    db_lead = db.query(_models.Leads).filter(_models.Leads.id == lead_id).first()
    if not db_lead:
        raise _fastapi.HTTPException(status_code=404, detail="Lead not found")
    
    for key, value in lead.model_dump(exclude_unset=True).items():
        setattr(db_lead, key, value)

    db_lead.updated_at = datetime.datetime.now()
    db.commit()
    db.refresh(db_lead)
    return db_lead


async def get_leads(db: _orm.Session,params):
    params=params.model_dump()
    optional_filters = []
    search_filters=[]
    

    if params.get('owner'):
        optional_filters.append(_user_model.User.first_name.ilike(f"%{params.get('owner')}%"))
        optional_filters.append(_user_model.User.last_name.ilike(f"%{params.get('owner')}%"))

    if params.get('status'):
        optional_filters.append(_models.Leads.status.ilike(f"%{params.get('status')}%"))
    if params.get('mobile'):
        optional_filters.append(_models.Leads.mobile.ilike(f"%{params.get('mobile')}%"))
    if params.get('source'):
        optional_filters.append(_user_model.Source.source.ilike(f"%{params.get('source')}%"))

    if params.get('search'):
        search_filters.append(_user_model.User.first_name.ilike(f"%{params.get('search')}%"))
        search_filters.append(_user_model.User.last_name.ilike(f"%{params.get('search')}%"))
        search_filters.append(_models.Leads.status.ilike(f"%{params.get('search')}%"))
        search_filters.append(_models.Leads.mobile.ilike(f"%{params.get('search')}%"))
        search_filters.append(_user_model.Source.source.ilike(f"%{params.get('search')}%")) 
    
    query = db.query(
        _models.Leads.id,
        _models.Leads.first_name,
        _models.Leads.mobile,
        _models.Leads.status,
        _user_model.Source.source,
        func.concat(_user_model.User.first_name,' ',_user_model.User.last_name).label('owner'),
        _models.Leads.lead_since
        
    ).join(
        _user_model.Source,
        _models.Leads.source_id == _user_model.Source.id
    ).outerjoin (
     _user_model.User,
     _models.Leads.staff_id ==_user_model.User.id).filter(_models.Leads.org_id == params.get('org_id'))
    
    print(query)
 
    if search_filters:
         query = query.filter(or_(*search_filters))

    if optional_filters:
        query = query.filter(and_(*optional_filters))
    
    leads = query.all()

    return leads


