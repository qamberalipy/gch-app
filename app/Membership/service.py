
from datetime import date
import jwt
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Membership.schema as _schemas
import app.Membership.models as _models
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
        
        
def create_membership_plan(plan: _schemas.MembershipPlanCreate, db: _orm.Session):
    db_plan = models.MembershipPlan(name=plan.name, price=plan.price, org_id=plan.org_id)
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_membership_plans_by_org_id(org_id: int, db: _orm.Session):
    return db.query(models.MembershipPlan).filter(
        models.MembershipPlan.org_id == org_id,
        models.MembershipPlan.is_deleted == False
    ).all()

def create_credit(credit: _schemas.CreditCreate,db: _orm.Session):
    db_credit = _models.Credits(
        name=credit.name,
        org_id=credit.org_id,
        min_limit=credit.min_limit,
        created_by=credit.created_by
    )
    db.add(db_credit)
    db.commit()
    db.refresh(db_credit)
    return db_credit

def update_credit(credit_id: int, credit: _schemas.CreditUpdate,db: _orm.Session):
    db_credit = db.query(_models.Credits).filter(_models.Credits.id == credit_id).first()
    if not db_credit:
        return None
    
    db_credit.name = credit.name
    db_credit.org_id = credit.org_id
    db_credit.min_limit = credit.min_limit
    db_credit.updated_by = credit.updated_by
    db.commit()
    db.refresh(db_credit)
    return db_credit

def delete_credit( credit_id: int,db: _orm.Session):
    db_credit = db.query(_models.Credits).filter(_models.Credits.id == credit_id).first()
    if not db_credit:
        return None
    
    db_credit.is_deleted = True
    db.commit()
    return db_credit

def get_credits_by_org_id( org_id: int,db: _orm.Session):
    return db.query(_models.Credits).filter(_models.Credits.org_id == org_id, _models.Credits.is_deleted == False).all()