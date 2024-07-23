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
import app.user.models as _usermodels
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
        
def create_coach(coach: _schemas.CoachCreate,db: _orm.Session):
    db_bank_detail = _usermodels.Bank_detail(
        org_id=coach.org_id,
        user_type="coach", 
        bank_name=coach.bank_name,
        iban_no=coach.iban_no,
        acc_holder_name=coach.acc_holder_name,
        swift_code=coach.swift_code,
        created_by=coach.created_by
    )
    db.add(db_bank_detail)
    db.commit()
    db.refresh(db_bank_detail)
    
    db_coach = _models.Coach(
        wallet_address=coach.wallet_address,
        own_coach_id=coach.own_coach_id,
        profile_img=coach.profile_img,
        first_name=coach.first_name,
        last_name=coach.last_name,
        dob=coach.dob,
        gender=coach.gender,
        email=coach.email,
        password=coach.password,
        phone=coach.phone,
        mobile_number=coach.mobile_number,
        notes=coach.notes,
        source_id=coach.source_id,
        country_id=coach.country_id,
        city=coach.city,
        zipcode=coach.zipcode,
        address_1=coach.address_1,
        address_2=coach.address_2,
        coach_since=coach.coach_since,
        created_by=coach.created_by,
        bank_detail_id=db_bank_detail.id
    )
    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)

    db_coach_org = _models.CoachOrganization(
        coach_id=db_coach.id,
        org_id=coach.org_id
    )
    db.add(db_coach_org)
    db.commit()
    db.refresh(db_coach_org)


    return db_coach

def update_coach(coach_id: int, coach: _schemas.CoachUpdate, db: _orm.Session):
    # Fetch the existing coach record
    db_coach = db.query(_models.Coach).filter(
        _models.Coach.id == coach_id,
        _models.Coach.is_deleted == False
    ).first()
    
    if not db_coach:
        return None  # Coach not found
    
    # Fetch the existing bank detail record
    db_bank_detail = db.query(_usermodels.Bank_detail).filter(
        _usermodels.Bank_detail.id == db_coach.bank_detail_id
    ).first()

    # Update bank details if provided
    if any([coach.bank_name, coach.iban_no, coach.acc_holder_name, coach.swift_code]):
        if not db_bank_detail:
            # Create new bank detail if not found
            db_bank_detail = _usermodels.Bank_detail(
                org_id=coach.org_id,
                user_type="coach",
                created_by=coach.updated_by
            )
            db.add(db_bank_detail)
        else:
            # Update existing bank detail
            db_bank_detail.org_id = coach.org_id if coach.org_id else db_bank_detail.org_id
            db_bank_detail.bank_name = coach.bank_name if coach.bank_name else db_bank_detail.bank_name
            db_bank_detail.iban_no = coach.iban_no if coach.iban_no else db_bank_detail.iban_no
            db_bank_detail.acc_holder_name = coach.acc_holder_name if coach.acc_holder_name else db_bank_detail.acc_holder_name
            db_bank_detail.swift_code = coach.swift_code if coach.swift_code else db_bank_detail.swift_code
            db_bank_detail.updated_by = coach.updated_by
        
        db.add(db_bank_detail)
        db.commit()
        db.refresh(db_bank_detail)
    
    # Update the coach details with provided fields only
    for field, value in coach.dict(exclude_unset=True).items():
        if hasattr(db_coach, field):
            setattr(db_coach, field, value)
    
    db_coach.updated_by = coach.updated_by

    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)

    return db_coach


def delete_coach(coach_id: int,db: _orm.Session):
    db_coach = db.query(models.Coach).filter(models.Coach.id == coach_id).first()
    if db_coach:
        db_coach.is_deleted = True
        db.commit()
        db.refresh(db_coach)

    return db_coach

def get_coach_by_id(coach_id: int,db: _orm.Session):
    db_coach = db.query(models.Coach,_models.CoachOrganization.org_id,
        _models.CoachOrganization.coach_status,
        _usermodels.Bank_detail.bank_name,
        _usermodels.Bank_detail.iban_no,
        _usermodels.Bank_detail.acc_holder_name,
        _usermodels.Bank_detail.swift_code).join(_models.CoachOrganization.coach_id==_models.Coach.id).join(_usermodels.Bank_detail.id==_models.Coach.bank_detail_id).filter(_models.Coach.id == coach_id,
        models.Coach.is_deleted == False).first()
 
    return db_coach

def get_all_coaches_by_org_id(org_id: int,db: _orm.Session):
    db_coach = db.query(models.Coach,_models.CoachOrganization.org_id,
        _models.CoachOrganization.coach_status,
        _usermodels.Bank_detail.bank_name,
        _usermodels.Bank_detail.iban_no,
        _usermodels.Bank_detail.acc_holder_name,
        _usermodels.Bank_detail.swift_code).join(_models.CoachOrganization.coach_id==_models.Coach.id).join(_usermodels.Bank_detail.id==_models.Coach.bank_detail_id).filter(_models.CoachOrganization.org_id == org_id,
        models.Coach.is_deleted == False).all()
 
    return db_coach