from datetime import date
from typing import List
import jwt
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Coach.schema as _schemas
import app.Coach.models as _models
import app.Client.models as _client_models
import app.user.models as _usermodels
import app.Shared.helpers as _helpers
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
        
def create_appcoach(coach: _schemas.CoachAppBase,db: _orm.Session):
   
    
    db_coach = _models.Coach(
        first_name=coach.first_name,
        last_name=coach.last_name,
        dob=coach.dob,
        gender=coach.gender,
        email=coach.email,
        phone=coach.phone,
        mobile_number=coach.mobile_number,
        notes=coach.notes,
        country_id=coach.country_id,
        city=coach.city,
        zipcode=coach.zipcode,
        address_1=coach.address_1,
        address_2=coach.address_2,
        coach_since=coach.coach_since,
        
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

    print("db_coach",db_coach)
    return db_coach

async def login_coach(email_address: str, wallet_address: str, db: _orm.Session = _fastapi.Depends(get_db)) -> dict:
    coach = await get_coach_by_email(email_address, db)
    
    if not coach:
        return {"is_registered": False}
    print("MYCLIENT: ",coach)
    coach.wallet_address = wallet_address
    db.commit()
    db.refresh(coach)
    
    token = _helpers.create_token(coach, "User")
    
    return {"is_registered": True,
            "coach":coach,
            "access_token":token
            }        

async def get_coach_by_email(email_address: str, db: _orm.Session = _fastapi.Depends(get_db)) -> _models.Coach:
    return db.query(_models.Coach).filter(models.Coach.email == email_address).first()


def create_bank_detail(coach: _schemas.CoachCreate, db: _orm.Session):
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
    return db_bank_detail

def create_coach_record(coach: _schemas.CoachCreate, db: _orm.Session, bank_detail_id: int):
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
        bank_detail_id=bank_detail_id
    )
    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)
    return db_coach

def create_coach_organization(coach_id: int, org_id: int, db: _orm.Session):
    db_coach_org = _models.CoachOrganization(
        coach_id=coach_id,
        org_id=org_id
    )
    db.add(db_coach_org)
    db.commit()
    db.refresh(db_coach_org)
    return db_coach_org

def create_client_coach_mappings(coach_id: int, member_ids: List[int], db: _orm.Session):
    for member_id in member_ids:
        db_client_coach = _client_models.ClientCoach(
            client_id=member_id,
            coach_id=coach_id
        )
        db.add(db_client_coach)
    db.commit()

def create_coach(coach: _schemas.CoachCreate, db: _orm.Session):
    coach_db = get_coach_by_email(coach.email, db)
    if coach_db:
            raise _fastapi.HTTPException(status_code=400, detail="Email already registered")
        
    db_bank_detail = create_bank_detail(coach, db)
    db_coach = create_coach_record(coach, db, db_bank_detail.id)
    create_coach_organization(db_coach.id, coach.org_id, db)

    if coach.member_ids:
        create_client_coach_mappings(db_coach.id, coach.member_ids, db)

    print("db_coach", db_coach)
    return db_coach


# def create_coach(coach: _schemas.CoachCreate,db: _orm.Session):
#     db_bank_detail = _usermodels.Bank_detail(
#         org_id=coach.org_id,
#         user_type="coach", 
#         bank_name=coach.bank_name,
#         iban_no=coach.iban_no,
#         acc_holder_name=coach.acc_holder_name,
#         swift_code=coach.swift_code,
#         created_by=coach.created_by
#     )
#     db.add(db_bank_detail)
#     db.commit()
#     db.refresh(db_bank_detail)
    
#     db_coach = _models.Coach(
#         wallet_address=coach.wallet_address,
#         own_coach_id=coach.own_coach_id,
#         profile_img=coach.profile_img,
#         first_name=coach.first_name,
#         last_name=coach.last_name,
#         dob=coach.dob,
#         gender=coach.gender,
#         email=coach.email,
#         password=coach.password,
#         phone=coach.phone,
#         mobile_number=coach.mobile_number,
#         notes=coach.notes,
#         source_id=coach.source_id,
#         country_id=coach.country_id,
#         city=coach.city,
#         zipcode=coach.zipcode,
#         address_1=coach.address_1,
#         address_2=coach.address_2,
#         coach_since=coach.coach_since,
#         created_by=coach.created_by,
#         bank_detail_id=db_bank_detail.id
#     )
#     db.add(db_coach)
#     db.commit()
#     db.refresh(db_coach)

#     db_coach_org = _models.CoachOrganization(
#         coach_id=db_coach.id,
#         org_id=coach.org_id
#     )
#     db.add(db_coach_org)
#     db.commit()
#     db.refresh(db_coach_org)

#     print("db_coach",db_coach)
#     return db_coach


# def update_coach(coach_id: int, coach: _schemas.CoachUpdate, db: _orm.Session):
#     # Fetch the existing coach record
#     db_coach = db.query(_models.Coach).filter(
#         _models.Coach.id == coach_id,
#         _models.Coach.is_deleted == False
#     ).first()
    
#     if not db_coach:
#         return None  # Coach not found
    
#     # Fetch the existing bank detail record
#     db_bank_detail = db.query(_usermodels.Bank_detail).filter(
#         _usermodels.Bank_detail.id == db_coach.bank_detail_id
#     ).first()

#     # Update bank details if provided
#     if any([coach.bank_name, coach.iban_no, coach.acc_holder_name, coach.swift_code]):
#         if not db_bank_detail:
#             # Create new bank detail if not found
#             db_bank_detail = _usermodels.Bank_detail(
#                 org_id=coach.org_id,
#                 user_type="coach",
#                 created_by=coach.updated_by
#             )
#             db.add(db_bank_detail)
#         else:
#             # Update existing bank detail
#             db_bank_detail.org_id = coach.org_id if coach.org_id else db_bank_detail.org_id
#             db_bank_detail.bank_name = coach.bank_name if coach.bank_name else db_bank_detail.bank_name
#             db_bank_detail.iban_no = coach.iban_no if coach.iban_no else db_bank_detail.iban_no
#             db_bank_detail.acc_holder_name = coach.acc_holder_name if coach.acc_holder_name else db_bank_detail.acc_holder_name
#             db_bank_detail.swift_code = coach.swift_code if coach.swift_code else db_bank_detail.swift_code
#             db_bank_detail.updated_by = coach.updated_by
        
#         db.add(db_bank_detail)
#         db.commit()
#         db.refresh(db_bank_detail)
    
#     # Update the coach details with provided fields only
#     for field, value in coach.dict(exclude_unset=True).items():
#         if hasattr(db_coach, field):
#             setattr(db_coach, field, value)
    
#     db_coach.updated_by = coach.updated_by

#     db.add(db_coach)
#     db.commit()
#     db.refresh(db_coach)

#     return db_coach

def update_bank_detail(coach: _schemas.CoachUpdate, db: _orm.Session, db_coach):
    db_bank_detail = db.query(_usermodels.Bank_detail).filter(
        _usermodels.Bank_detail.id == db_coach.bank_detail_id
    ).first()

    if any([coach.bank_name, coach.iban_no, coach.acc_holder_name, coach.swift_code]):
        if not db_bank_detail:
            db_bank_detail = _usermodels.Bank_detail(
                org_id=coach.org_id,
                user_type="coach",
                created_by=coach.updated_by
            )
            db.add(db_bank_detail)
        else:
            db_bank_detail.org_id = coach.org_id if coach.org_id else db_bank_detail.org_id
            db_bank_detail.bank_name = coach.bank_name if coach.bank_name else db_bank_detail.bank_name
            db_bank_detail.iban_no = coach.iban_no if coach.iban_no else db_bank_detail.iban_no
            db_bank_detail.acc_holder_name = coach.acc_holder_name if coach.acc_holder_name else db_bank_detail.acc_holder_name
            db_bank_detail.swift_code = coach.swift_code if coach.swift_code else db_bank_detail.swift_code
            db_bank_detail.updated_by = coach.updated_by
        
        db.add(db_bank_detail)
        db.commit()
        db.refresh(db_bank_detail)

    return db_bank_detail

def update_coach_record(coach: _schemas.CoachUpdate, db: _orm.Session, db_coach):
    for field, value in coach.dict(exclude_unset=True).items():
        if hasattr(db_coach, field):
            setattr(db_coach, field, value)
    
    db_coach.updated_by = coach.updated_by

    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)
    
    return db_coach

def update_client_coach_mappings(coach_id: int, member_ids: List[int], db: _orm.Session):
    db.query(_client_models.ClientCoach).filter(_client_models.ClientCoach.coach_id == coach_id).delete()
    for member_id in member_ids:
        db_client_coach = _client_models.ClientCoach(
            client_id=member_id,
            coach_id=coach_id
        )
        db.add(db_client_coach)
    db.commit()

def update_coach(coach: _schemas.CoachUpdate, db: _orm.Session):
    db_coach = db.query(_models.Coach).filter(
        _models.Coach.id == coach.id,
        _models.Coach.is_deleted == False
    ).first()
    
    if not db_coach:
        return None

    db_bank_detail = update_bank_detail(coach, db, db_coach)
    
    db_coach.bank_detail_id = db_bank_detail.id if db_bank_detail else db_coach.bank_detail_id
    db_coach = update_coach_record(coach, db, db_coach)
    
    if coach.member_ids:
        update_client_coach_mappings(db_coach.id, coach.member_ids, db)

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

def get_all_coaches_by_org_id(org_id: int, db: _orm.Session):
    # Perform the join operations correctly and filter by org_id and is_deleted status

    # db_coaches = db.query(
    #     _models.Coach.id,
    #     _models.Coach.wallet_address,
    #     _models.Coach.own_coach_id,
    #     _models.Coach.profile_img,
    #     _models.Coach.first_name,
    #     _models.Coach.last_name,
    #     _models.Coach.dob,
    #     _models.Coach.gender,
    #     _models.Coach.email,
    #     _models.Coach.password,
    #     _models.Coach.phone,
    #     _models.Coach.mobile_number,
    #     _models.Coach.notes,
    #     _models.Coach.source_id,
    #     _models.Coach.country_id,
    #     _models.Coach.city,
    #     _models.Coach.zipcode,
    #     _models.Coach.address_1,
    #     _models.Coach.address_2,
    #     _models.Coach.coach_since,
    #     _usermodels.Bank_detail.bank_name,
    #     _usermodels.Bank_detail.iban_no,
    #     _usermodels.Bank_detail.acc_holder_name,
    #     _usermodels.Bank_detail.swift_code,
    #     _models.Coach.created_at,
    #     _models.Coach.updated_at
    # ).join(
    #     _models.CoachOrganization, _models.Coach.id == _models.CoachOrganization.coach_id
    # ).join(
    #     _usermodels.Bank_detail, _models.Coach.bank_detail_id == _usermodels.Bank_detail.id
    # ).filter(
    #     _models.CoachOrganization.org_id == org_id,
    #     _models.Coach.is_deleted == False
    # ).all()
    
    db_coaches = db.query(
        *_models.Coach.__table__.columns,
        *_usermodels.Bank_detail.__table__.columns,
        *_models.CoachOrganization.__table__.columns,
    ).join(
        _models.CoachOrganization, _models.Coach.id == _models.CoachOrganization.coach_id
    ).join(
        _usermodels.Bank_detail, _models.Coach.bank_detail_id == _usermodels.Bank_detail.id
    ).filter(
        _models.CoachOrganization.org_id == org_id,
        _models.Coach.is_deleted == False
    ).all()
    print("ALL COACH",db_coaches)
    return db_coaches
