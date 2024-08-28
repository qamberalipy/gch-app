from datetime import date,datetime as dt
from app.Exercise.service import extract_columns
from typing import Annotated,Any, List
import jwt
from sqlalchemy import String, asc, cast, desc, func, literal_column, or_, text
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
from sqlalchemy.orm import aliased

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

async def get_coach_organzation(email: str, db: _orm.Session) -> List[_schemas.CoachOrganizationResponse]:
    db_client = db.query(
        _usermodels.Organization.id,
        _usermodels.Organization.name,
        _usermodels.Organization.profile_img
    ).join(
        _models.CoachOrganization,
        _models.CoachOrganization.org_id == _usermodels.Organization.id
    ).join(
        _models.Coach,
        _models.Coach.id == _models.CoachOrganization.coach_id and _models.Coach.email == email
    ).filter(
        _models.Coach.email == email
    ).all()
    return db_client

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

# async def login_coach(
#     email_address: str,
#     wallet_address: str,
#     db: _orm.Session = _fastapi.Depends(get_db),
# ) -> dict:
#     coach = await get_coach_by_email(email_address, db)

#     if not coach:
#         return {"is_registered": False}

#     setattr(coach, wallet_address, wallet_address)
#     db.commit()
#     db.refresh(coach)

#     token = _helpers.create_token(dict(id=coach.id), "Coach")

#     return {"is_registered": True, "coach": coach, "access_token": token}


async def login_coach(
    email_address: str,
    wallet_address: str='',
    db: _orm.Session = _fastapi.Depends(get_db),
) -> dict:

    query = (
        db.query(
            *_models.Coach.__table__.columns,
            _models.CoachOrganization.own_coach_id,
            func.array_agg(
                func.json_build_object(
                    'id', func.coalesce(_models.CoachOrganization.org_id, 0),
                    'name', func.coalesce(_usermodels.Organization.name, ""),
                    'profile_url', func.coalesce(_usermodels.Organization.profile_img, "")
                )
            ).label('organizations')
        )
        .outerjoin(
            models.CoachOrganization,
            models.CoachOrganization.coach_id == models.Coach.id
        )
        .outerjoin(
            _usermodels.Organization,
            _usermodels.Organization.id == models.CoachOrganization.org_id
        )
        .filter(
            models.Coach.email == email_address,
            models.Coach.is_deleted == False
        )
        .group_by(
            *_models.Coach.__table__.columns,
            _models.CoachOrganization.own_coach_id,
        )
    )

    coach = query.first()

    if not coach:
        return {"is_registered": False}

    coach_dict = coach._asdict()
    # coach_dict["wallet_address"] = wallet_address
    print("coach_dict: ",coach_dict)

    # db.commit()
    # db.refresh(coach)

    token = _helpers.create_token(dict(id=coach.id), "Coach")

    return {"is_registered": True, "coach": coach_dict, "access_token": token}

async def get_coach_by_email(
    email_address: str, db: _orm.Session = _fastapi.Depends(get_db)
) -> _models.Coach:

    db_coach = db.query(
        _models.Coach.id,
        _models.Coach.first_name,
        _models.Coach.last_name,
        _models.Coach.email,
        _models.Coach.is_deleted,
        func.array_agg(_models.CoachOrganization.org_id).label('org_ids')
        ).join(
            _models.CoachOrganization,and_(_models.CoachOrganization.coach_id==_models.Coach.id,_models.CoachOrganization.is_deleted==False)    
        ).filter(
            models.Coach.email == email_address
        ).group_by(
            _models.Coach.id,   
            _models.Coach.first_name,
            _models.Coach.last_name,
            _models.Coach.email,
        ).first()
    return db_coach


def create_bank_detail(coach: _schemas.CoachCreate,user_id,db: _orm.Session):
    db_bank_detail = _usermodels.Bank_detail(
        org_id=coach.org_id,
        user_type="coach", 
        bank_name=coach.bank_name,
        iban_no=coach.iban_no,
        acc_holder_name=coach.acc_holder_name,
        swift_code=coach.swift_code,
        created_by=user_id,
        updated_by=user_id)
    db.add(db_bank_detail)
    db.commit()
    db.refresh(db_bank_detail)
    return db_bank_detail

def create_coach_record(coach: _schemas.CoachCreate, db: _orm.Session,user_id,bank_detail_id: int):
    db_coach = _models.Coach(
        wallet_address=coach.wallet_address,
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
        bank_detail_id=bank_detail_id,
        created_by=user_id,
        updated_by=user_id,
        created_at=dt.now(),
        updated_at=dt.now())
    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)
    return db_coach

def create_coach_organization(coach_id: int, org_id: int, coach_status:str,own_coach_id,db: _orm.Session):
    db_coach_org = _models.CoachOrganization(
        coach_id=coach_id,
        org_id=org_id,
        coach_status=coach_status,
        own_coach_id=own_coach_id,
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

async def create_coach(coach: _schemas.CoachCreate,user_id, db: _orm.Session=_fastapi.Depends(get_db)):
    coach_db = await get_coach_by_email(coach.email,db=db)
    if coach_db:
        if coach.org_id in coach_db.org_ids:
            print("coach exists within the same organization")
            raise _fastapi.HTTPException(status_code=400, detail="Email already registered")
        else:
            print("coach does not exist within the same organization")
            db_bank_detail = create_bank_detail(coach,user_id,db)
            db_coach = update_app_coach_record(coach_db.id,coach,db)
            create_coach_organization(coach_db.id, coach.org_id, coach.coach_status,coach.own_coach_id,db)
            if coach.member_ids:
                create_client_coach_mappings(coach_db.id, coach.member_ids, db)
        
            return {
                "status_code": "201",
                "id": coach_db.id,
                "message": "Coach created successfully"
            }

        
    db_bank_detail = create_bank_detail(coach,user_id,db)
    db_coach = create_coach_record(coach, db,user_id,db_bank_detail.id)
    create_coach_organization(db_coach.id, coach.org_id, coach.coach_status,coach.own_coach_id ,db)

    if coach.member_ids:
        create_client_coach_mappings(db_coach.id, coach.member_ids, db)

    return {
            "status_code": "201",
            "id": db_coach.id,
            "message": "Coach created successfully"
        }


def get_coach_list(org_id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    query = (
        db.query(
            _models.Coach.id,
            func.concat(_models.Coach.first_name, ' ', _models.Coach.last_name).label('name')
        )
        .join(
            _models.CoachOrganization,
            _models.Coach.id == _models.CoachOrganization.coach_id
        )
        .filter(
            and_(
                _models.CoachOrganization.org_id == org_id,
                _models.CoachOrganization.is_deleted == False,
                _models.Coach.is_deleted == False
            )
        )
    )
    return query.all()

def update_bank_detail(coach: _schemas.CoachUpdate,user_id,db: _orm.Session, db_coach):
    db_bank_detail = db.query(_usermodels.Bank_detail).filter(
        _usermodels.Bank_detail.id == db_coach.bank_detail_id
    ).first()

    if any([coach.bank_name, coach.iban_no, coach.acc_holder_name, coach.swift_code]):
        if not db_bank_detail:
            db_bank_detail = _usermodels.Bank_detail(
                org_id=coach.org_id,
                user_type="coach",
                created_by=user_id,
                updated_by=user_id
            )
            db.add(db_bank_detail)
        else:
            db_bank_detail.org_id = coach.org_id if coach.org_id else db_bank_detail.org_id
            db_bank_detail.bank_name = coach.bank_name if coach.bank_name else db_bank_detail.bank_name
            db_bank_detail.iban_no = coach.iban_no if coach.iban_no else db_bank_detail.iban_no
            db_bank_detail.acc_holder_name = coach.acc_holder_name if coach.acc_holder_name else db_bank_detail.acc_holder_name
            db_bank_detail.swift_code = coach.swift_code if coach.swift_code else db_bank_detail.swift_code
            db_bank_detail.updated_by = user_id
        
        db.add(db_bank_detail)
        db.commit()
        db.refresh(db_bank_detail)

    return db_bank_detail

def update_coach_record(coach: _schemas.CoachUpdate, db: _orm.Session,user_id,db_coach):
    for field, value in coach.dict(exclude_unset=True).items():
        if hasattr(db_coach, field):
            setattr(db_coach, field, value)
    
    db_coach.updated_by = user_id
    db_coach.updated_at=dt.now()
    db.add(db_coach)
    db.commit()
    db.refresh(db_coach)
    
    return db_coach

async def update_app_coach_record(coach_id: int, coach: _schemas.CoachAppUpdate, db: _orm.Session):
    # Fetch the coach record from the database
    db_coach = db.query(_models.Coach).filter(_models.Coach.id == coach_id).first()

    if not db_coach:
        return None  # or raise an exception
    coach.is_deleted=False
    # Update the fields that are set in the incoming `coach` data
    for field, value in coach.dict(exclude_unset=True).items():
        setattr(db_coach, field, value)
    
    # Commit the changes and refresh the object
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

def update_coach_organization(coach_id: int, org_id: int, coach_status: str, db: _orm.Session):
    db_coach_org = db.query(_models.CoachOrganization).filter(
        _models.CoachOrganization.coach_id == coach_id,
        _models.CoachOrganization.is_deleted == False
    ).first()

    if not db_coach_org:
        db_coach_org = _models.CoachOrganization(
            coach_id=coach_id,
            org_id=org_id,
            coach_status=coach_status,
            is_deleted=False
        )
        db.add(db_coach_org)
    else:
        db_coach_org.org_id = org_id if org_id else db_coach_org.org_id
        db_coach_org.coach_status = coach_status if coach_status else db_coach_org.coach_status

        db.add(db_coach_org)

    db.commit()
    db.refresh(db_coach_org)
    
    return db_coach_org


async def update_coach(coach_id:int , coach: _schemas.CoachUpdate,Type:str,user_id,db: _orm.Session):
    print("MY DB 2",coach_id,coach)
    db_coach = db.query(
            _models.Coach
        ).join(
            _models.CoachOrganization, and_(_models.Coach.id == _models.CoachOrganization.coach_id,_models.CoachOrganization.org_id==coach.org_id,_models.CoachOrganization.is_deleted==False)
        ).first()
        
    print("MY DB",db_coach)
    if not db_coach:
        return None

    db_bank_detail = update_bank_detail(coach,user_id,db, db_coach)
    db_coach.bank_detail_id = db_bank_detail.id if db_bank_detail else db_coach.bank_detail_id
    db_coach = update_coach_record(coach, db,user_id, db_coach)
    
    if coach.member_ids:
        update_client_coach_mappings(db_coach.id, coach.member_ids, db)
    
    db_coach_org = update_coach_organization(
        coach_id=coach_id,
        org_id=coach.org_id,
        coach_status=coach.coach_status,
        db=db
    )
    if Type=="app":
        return db_coach
    return db_coach

def delete_coach(coach_id: int, org_id: int, db: _orm.Session):
    db_coach = db.query(_models.CoachOrganization).filter(
        and_(
            _models.CoachOrganization.coach_id == coach_id,
            _models.CoachOrganization.org_id == org_id
        )
    ).first()

    if db_coach:
        db_coach.is_deleted = True
        db.commit()
        db.refresh(db_coach)
        return {"status": "201", "detail": "Coach deleted successfully"}
    else:
        raise _fastapi.HTTPException(status_code=404, detail="Coach not found")

    return {"status":"201","detail":"Coach deleted successfully"}

def get_coach_by_id(coach_id: int,org_id:int,db: _orm.Session):
    
    CoachOrg = aliased(_models.CoachOrganization)
    BankDetail = aliased(_usermodels.Bank_detail)
    ClientCoach = aliased(_client_models.ClientCoach)
    
    query = db.query(
        *_models.Coach.__table__.columns,
        CoachOrg.coach_status,
        CoachOrg.org_id,
        CoachOrg.check_in,     
        CoachOrg.own_coach_id,
        BankDetail.bank_name,
        BankDetail.iban_no,
        BankDetail.acc_holder_name,
        BankDetail.swift_code,
        func.array_agg(
            func.json_build_object(
                'id', func.coalesce(ClientCoach.client_id, 0),
                'name', func.concat(
                    func.coalesce(_client_models.Client.first_name, ""), 
                    ' ', 
                    func.coalesce(_client_models.Client.last_name, "")
                )
            )
        ).label('members')
    ).join(
        CoachOrg, and_(_models.Coach.id == CoachOrg.coach_id,CoachOrg.org_id==org_id,CoachOrg.is_deleted==False)
    ).outerjoin(
        BankDetail, _models.Coach.bank_detail_id == BankDetail.id
    ).outerjoin(
        ClientCoach, ClientCoach.coach_id == _models.Coach.id
    ).outerjoin(
        _client_models.Client,  _client_models.Client.id == ClientCoach.client_id
    ).filter(
        _models.Coach.id == coach_id,
        _models.Coach.is_deleted == False
    ).group_by(
        _models.Coach.id,
        CoachOrg.coach_status,
        CoachOrg.org_id,
        CoachOrg.check_in,     
        CoachOrg.own_coach_id,
        BankDetail.bank_name,
        BankDetail.iban_no,
        BankDetail.acc_holder_name,
        BankDetail.swift_code
    )
    
    db_coach = query.first()
    
    if db_coach:
        return _schemas.CoachReadSchema(**db_coach._asdict())
    else:
        return None
    
# def get_all_coaches_by_org_id(org_id: int, db: _orm.Session, params: _schemas.CoachFilterParams):
#     sort_order = desc(_models.Coach.created_at) if params.sort_order == "desc" else asc(_models.Coach.created_at)
#     CoachOrg = aliased(_models.CoachOrganization)
#     BankDetail = aliased(_usermodels.Bank_detail)
#     ClientCoach = aliased(_client_models.ClientCoach)
    
#     query = db.query(
#         *_models.Coach.__table__.columns,
#         CoachOrg.coach_status,
#         CoachOrg.org_id,
#         BankDetail.bank_name,
#         BankDetail.iban_no,
#         BankDetail.acc_holder_name,
#         BankDetail.swift_code,
#         func.array_agg(func.coalesce(ClientCoach.client_id,0)).label('member_ids').label('member_ids')
#     ).join(
#         CoachOrg, _models.Coach.id == CoachOrg.coach_id
#     ).join(
#         BankDetail, _models.Coach.bank_detail_id == BankDetail.id
#     ).join(
#         ClientCoach, ClientCoach.coach_id == _models.Coach.id
#     ).filter(
#         _models.Coach.is_deleted == False,
#         CoachOrg.org_id == org_id
#     ).order_by(sort_order).group_by(
#         _models.Coach.id,
#         CoachOrg.coach_status,
#         CoachOrg.org_id,
#         BankDetail.bank_name,
#         BankDetail.iban_no,
#         BankDetail.acc_holder_name,
#         BankDetail.swift_code)
    
#     if params.search_key:
#         query = query.filter(or_(
#             _models.Coach.first_name.ilike(params.search_key),
#             _models.Coach.last_name.ilike(params.search_key),
#             _models.Coach.email.ilike(params.search_key),
#             _models.Coach.mobile_number.ilike(params.search_key),
#             _models.Coach.own_coach_id.ilike(params.search_key),
#             _models.Coach.gender.ilike(params.search_key),
#             _models.Coach.phone.ilike(params.search_key)
#         ))
        
#     if params.status is not None:
#         query = query.filter(CoachOrg.coach_status == params.status)

#     query = query.offset(params.offset).limit(params.limit)
#     db_coaches = query.all()

#     coaches = []
#     for coach in db_coaches:
#         coaches.append(_schemas.CoachReadSchema(**coach._asdict()))

#     if coaches:
#         return coaches
#     else:
#         return None
    
from sqlalchemy import text, func, asc, desc, or_
from sqlalchemy.orm import aliased

def get_all_coaches_by_org_id(org_id: int, db: _orm.Session, params: _schemas.CoachFilterParams):
    CoachOrg = aliased(_models.CoachOrganization)
    BankDetail = aliased(_usermodels.Bank_detail)
    ClientCoach = aliased(_client_models.ClientCoach)
    Client = aliased(_client_models.Client)

    # Define the sort mapping using aliases
    sort_mapping = {
        "first_name": text("coach.first_name"),
        "last_name": text("coach.last_name"),
        "coach_status": text("coach_status"),
        "own_coach_id": text("coach.own_coach_id"),
        "last_online": text("coach.last_online"),
        "check_in": text("coach.check_in"),
        "created_at":text("coach.created_at")
    }
    # Main query
    query = db.query(
        *_models.Coach.__table__.columns,
        CoachOrg.coach_status,
        CoachOrg.org_id,
        CoachOrg.check_in,     
        CoachOrg.own_coach_id,
        BankDetail.bank_name,
        BankDetail.iban_no,
        BankDetail.acc_holder_name,
        BankDetail.swift_code,
        func.array_agg(func.coalesce(ClientCoach.client_id, 0)).label('members')
    ).select_from(_models.Coach).join(
        CoachOrg, and_(_models.Coach.id == CoachOrg.coach_id,CoachOrg.org_id==org_id,CoachOrg.is_deleted==False)
    ).outerjoin(
        BankDetail, _models.Coach.bank_detail_id == BankDetail.id
    ).outerjoin(
        ClientCoach, ClientCoach.coach_id == _models.Coach.id
    ).outerjoin(
        Client,and_(Client.id == ClientCoach.client_id,Client.is_deleted==False)
    ).filter(
        _models.Coach.is_deleted == False,
        CoachOrg.org_id == org_id
    ).group_by(
        _models.Coach.id,
        CoachOrg.coach_status,
        CoachOrg.org_id,
        CoachOrg.check_in,     
        CoachOrg.own_coach_id,
        BankDetail.bank_name,
        BankDetail.iban_no,
        BankDetail.acc_holder_name,
        BankDetail.swift_code
    )

    # Subquery for total counts
    total_counts = db.query(func.count()).select_from(query.subquery()).scalar()

    # Apply search filters
    if params.search_key:
        query = query.filter(or_(
            _models.Coach.first_name.ilike(f"%{params.search_key}%"),
            _models.Coach.last_name.ilike(f"%{params.search_key}%"),
            _models.Coach.own_coach_id.ilike(f"%{params.search_key}%"),
            _models.Coach.email.ilike(f"%{params.search_key}%"),
            _models.Coach.mobile_number.ilike(f"%{params.search_key}%"),
            _models.Coach.gender.ilike(f"%{params.search_key}%"),
            _models.Coach.phone.ilike(f"%{params.search_key}%")
        ))

    # Apply status filter
    if params.status is not None:
        query = query.filter(CoachOrg.coach_status == params.status)
    
    if params.sort_key in sort_mapping.keys():
        sort_column = sort_mapping.get(params.sort_key)
        sort_order = desc(sort_column) if params.sort_order == "desc" else asc(sort_column)
        query = query.order_by(sort_order)
    elif params.sort_key is not None:
        raise _fastapi.HTTPException(status_code=400, detail="Sorting column not found.")

    filtered_counts = db.query(func.count()).select_from(query.subquery()).scalar()

 
    query = query.offset(params.offset).limit(params.limit)
    db_coaches = query.all()

    coaches = [_schemas.CoachResponse.from_orm(coach) for coach in db_coaches]

    return {"data": coaches, "total_counts": total_counts, "filtered_counts": filtered_counts}


async def get_total_coaches(org_id: int, db: _orm.Session = _fastapi.Depends(get_db)) -> int:
    total_coaches = db.query(func.count(models.Coach.id)).join(
        _models.CoachOrganization,
        _models.CoachOrganization.coach_id == models.Coach.id
    ).filter(
        _models.CoachOrganization.org_id == org_id
    ).scalar()
    return total_coaches

def get_filters(

    search_key: Annotated[str, _fastapi.Query(title="Search Key")] = None,
    status: Annotated[str , _fastapi.Query(title="Status")] = None,
    sort_order: Annotated[str,_fastapi.Query(title="Sort Order")]="desc",
    sort_key: Annotated[str,_fastapi.Query(title="Sort Key")]=None,
    limit: Annotated[int, _fastapi.Query(description="Pagination Limit")] = None,
    offset: Annotated[int, _fastapi.Query(description="Pagination offset")] = None):
    
    return _schemas.CoachFilterParams(
        search_key=search_key,
        sort_order=sort_order,
        sort_key=sort_key,
        status=status,
        limit=limit,
        offset = offset
    )

