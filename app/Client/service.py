from datetime import date
import datetime
import string
from typing import List
import jwt
from pydantic import ValidationError
from sqlalchemy import asc, case, desc, func, or_, text
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Client.schema as _schemas
import app.Client.models as _models
import app.Coach.models as _coach_models
import app.Shared.helpers as _helpers
import app.user.models as _user_models
import random
import json
import pika
import time
import os
import bcrypt as _bcrypt
from . import models, schema
from app.Exercise.service import extract_columns

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

async def get_client_organzation(email: str, db: _orm.Session) -> List[_schemas.ClientOrganizationResponse]:
    db_client = db.query(
        _user_models.Organization.id,
        _user_models.Organization.name,
        _user_models.Organization.profile_img
    ).join(
        _models.ClientOrganization,
        _models.ClientOrganization.org_id == _user_models.Organization.id
    ).join(
        _models.Client,
        _models.Client.id == _models.ClientOrganization.client_id
    ).filter(
        _models.Client.email == email
    ).all()
    
    # organizations = [_schemas.ClientOrganizationResponse(id=org.id, name=org.name, profile_img=org.profile_img) for org in db_client]
    return db_client


def generate_own_member_id():
    random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"guest{random_string}"


async def create_client(
    client: _schemas.RegisterClient, db: _orm.Session = _fastapi.Depends(get_db)
):
    db_client = _models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


async def create_client_for_app(
    client: _schemas.RegisterClientApp, db: _orm.Session = _fastapi.Depends(get_db)
):
    db_client = _models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


async def create_client_organization(
    client_organization: _schemas.CreateClientOrganization,
    db: _orm.Session = _fastapi.Depends(get_db),
):
    db_client_organization = _models.ClientOrganization(**client_organization.dict())
    db.add(db_client_organization)
    db.commit()
    db.refresh(db_client_organization)
    return db_client_organization


async def create_client_membership(
    client_membership: _schemas.CreateClientMembership,
    db: _orm.Session = _fastapi.Depends(get_db),
):
    db_client_membership = _models.ClientMembership(**client_membership.dict())
    db.add(db_client_membership)
    db.commit()
    db.refresh(db_client_membership)
    return db_client_membership


async def create_client_coach(client_id : int, coach_ids : List[int], db: _orm.Session = _fastapi.Depends(get_db)):
    member_coach = [
        _models.ClientCoach(client_id=client_id, coach_id=coach_id)
        for coach_id in coach_ids
    ]
    db.add_all(member_coach)
    db.commit()
    return member_coach


async def authenticate_client(
    email_address: str, db: _orm.Session = _fastapi.Depends(get_db)
):
    client = get_client_by_email(email_address, db)

    if not client:
        return False

    return client


async def login_client(
    email_address: str,
    wallet_address: str,
    db: _orm.Session = _fastapi.Depends(get_db),
) -> dict:

    query = (
        db.query(
            *_models.Client.__table__.columns,
            func.array_agg(
                func.json_build_object(
                    'id', func.coalesce(models.ClientOrganization.org_id, 0),
                    'name', func.coalesce(_user_models.Organization.name, ""),
                    'profile_url', func.coalesce(_user_models.Organization.profile_img, "")
                )
            ).label('organizations')
        )
        .outerjoin(
            models.ClientOrganization,
            models.ClientOrganization.client_id == models.Client.id
        )
        .outerjoin(
            _user_models.Organization,
            _user_models.Organization.id == models.ClientOrganization.org_id
        )
        .filter(
            models.Client.email == email_address,
            models.Client.is_deleted == False
        )
        .group_by(
            *_models.Client.__table__.columns
        )
    )

    client = query.first()

    if not client:
        return {"is_registered": False}

    client_dict = client._asdict()
    # client_dict["wallet_address"] = wallet_address
    print("client_dict: ",client_dict)

    # db.commit()
    # db.refresh(client)

    token = _helpers.create_token(dict(id=client.id), "Member")

    return {"is_registered": True, "client": client_dict, "access_token": token}

async def get_client_by_email(
    email_address: str, db: _orm.Session = _fastapi.Depends(get_db)
) -> models.Client:
    return db.query(models.Client).filter(models.Client.email == email_address).first()


async def get_business_clients(
    org_id: int, db: _orm.Session = _fastapi.Depends(get_db)
):
    clients = (
        db.query(models.Client.id, models.Client.first_name)
        .join(
            models.ClientOrganization,
            models.ClientOrganization.client_id == models.Client.id,
        )
        .filter(
            models.ClientOrganization.org_id == org_id,
            models.Client.is_business == True,
        )
        .all()
    )

    return clients


async def update_client(
    client_id: int,
    client: _schemas.ClientUpdate,
    db: _orm.Session = _fastapi.Depends(get_db),
):
    db_client = db.query(_models.Client).filter(and_(_models.Client.id == client_id,_models.Client.is_deleted == False)).first()

    if not db_client:
        raise _fastapi.HTTPException(status_code=404, detail="Member not found")
    
    for key, value in client.dict(exclude_unset=True).items():
        setattr(db_client, key, value)

    db_client_status=db.query(_models.ClientOrganization).filter(and_(_models.ClientOrganization.client_id == client_id,_models.ClientOrganization.org_id == client.org_id)).first()    
    
    if not db_client_status:
        raise _fastapi.HTTPException(status_code=404, detail="Please enter correct organization of member")
        
    db_client_status.client_status = client.status
        
    db_client.updated_at = datetime.datetime.now()
    db.commit()
    
    db.refresh(db_client)
    db.refresh(db_client_status)
    
    return db_client


async def update_client_membership(
    client_id: int, membership_id: int, db: _orm.Session = _fastapi.Depends(get_db)
):
    db_client_membership = (
        db.query(_models.ClientMembership)
        .filter(_models.ClientMembership.client_id == client_id)
        .first()
    )
    if not db_client_membership:
        db_client_membership = _models.ClientMembership(
            client_id=client_id, membership_plan_id=membership_id
        )
        db.add(db_client_membership)
    else:
        db_client_membership.membership_plan_id = membership_id

    db.commit()
    db.refresh(db_client_membership)
    return db_client_membership


async def update_client_coach(client_id: int, coach_ids: List[int], db: _orm.Session = _fastapi.Depends(get_db)):
    existing_coaches = db.query(_models.ClientCoach).filter(_models.ClientCoach.client_id == client_id).all()
    existing_coach_ids = {coach.coach_id for coach in existing_coaches}

    # Coaches to add
    new_coach_ids = set(coach_ids)
    coaches_to_add = new_coach_ids - existing_coach_ids

    # Coaches to remove
    coaches_to_remove = existing_coach_ids - new_coach_ids

    # Remove coaches
    if coaches_to_remove:
        db.query(_models.ClientCoach).filter(
            _models.ClientCoach.client_id == client_id,
            _models.ClientCoach.coach_id.in_(coaches_to_remove)
        ).delete(synchronize_session=False)

    # Add new coaches
    for coach_id in coaches_to_add:
        db.add(_models.ClientCoach(client_id=client_id, coach_id=coach_id))


    db.commit()
    return db.query(_models.ClientCoach).filter(_models.ClientCoach.client_id == client_id).all()

async def update_app_client(
    client_id: int,
    client: _schemas.ClientUpdate,
    db: _orm.Session = _fastapi.Depends(get_db),
):
    db_client = db.query(_models.Client).filter(_models.Client.id == client_id).first()

    if not db_client:
        raise _fastapi.HTTPException(status_code=404, detail="Member not found")
    client.is_deleted=False
    for key, value in client.dict(exclude_unset=True).items():
        setattr(db_client, key, value)
     
    db_client.updated_at = datetime.datetime.now()
    db.commit()
    
    db.refresh(db_client)
    
    return db_client

async def delete_client(client_id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    db_client = db.query(_models.Client).filter(and_(_models.Client.id == client_id,_models.Client.is_deleted == False)).first()
    if not db_client:
        raise _fastapi.HTTPException(status_code=404, detail="Member not found")

    db_client.is_deleted = True
    db_client.updated_at = datetime.datetime.now()
    db.commit()
    db.refresh(db_client)
    return {"status":"201","detail":"Member deleted successfully"}


def get_list_clients(
    org_id: int, db: _orm.Session = _fastapi.Depends(get_db)
) -> List[models.Client]:
    return (
        db.query(_models.Client.id,func.concat(_models.Client.first_name,' ',_models.Client.last_name).label('name'))
        .join(
            _models.ClientOrganization,
            _models.Client.id == _models.ClientOrganization.client_id,
        )
        .filter(_models.ClientOrganization.org_id == org_id)
        .filter(_models.Client.is_deleted == False)
        .all()
    )


async def get_total_clients(
    org_id: int, db: _orm.Session = _fastapi.Depends(get_db)
) -> int:
    total_clients = (
        db.query(func.count(models.Client.id))
        .join(
            models.ClientOrganization,
            models.ClientOrganization.client_id == models.Client.id,
        )
        .filter(models.ClientOrganization.org_id == org_id)
        .scalar()
    )

    return total_clients


# def get_filtered_clients(
#     db: _orm.Session,
#     org_id:int,
#     params: _schemas.ClientFilterParams

# ) -> List[_schemas.ClientFilterRead]:
#     # Create a base query with the necessary joins
    
#     query = db.query(
#         _models.Client.id,
#         _models.Client.own_member_id,
#         _models.Client.first_name,
#         _models.Client.last_name,
#         _models.Client.phone,
#         _models.Client.mobile_number,
#         _models.Client.check_in,
#         _models.Client.last_online,
#         _models.Client.client_since,
#         func.coalesce(
#             _models.Client.first_name,
#             db.query(_models.Client.first_name).filter(_models.Client.id == _models.Client.business_id)
#         ).label("business_name"),
#         _coach_models.Coach.first_name.label("coach_name")
#     ).join(
#         _models.ClientOrganization, _models.Client.id == _models.ClientOrganization.client_id
#     ).join(
#         _models.ClientCoach, _models.Client.id == _models.ClientCoach.client_id
#     ).join(
#         _models.ClientMembership, _models.Client.id == _models.ClientMembership.client_id
#     ).join(
#         _coach_models.Coach, _models.ClientCoach.coach_id == _coach_models.Coach.id
#     ).filter(
#         _models.ClientOrganization.org_id == org_id,
#         _models.ClientOrganization.is_deleted == False,
#         _models.Client.is_deleted==False,
#         _coach_models.Coach.is_deleted == False
#     )

#     sort_order = (
#         desc(_models.Client.created_at)
#         if params.sort_order == "desc"
#         else asc(_models.Client.created_at)
#     )

#     # Apply filters conditionally

#     if params.member_name:
#         query = query.filter(or_(
#             _models.Client.first_name.ilike(f"%{params.member_name}%"),
#             _models.Client.last_name.ilike(f"%{params.member_name}%")
#         ))

#     if params.status:
#         query = query.filter(
#             _models.ClientOrganization.client_status.ilike(f"%{params.status}%")
#         )

#     if params.coach_assigned:
#         query = query.filter(_models.ClientCoach.coach_id == params.coach_assigned)

#     if params.membership_plan:
#         query = query.filter(
#             _models.ClientMembership.membership_plan_id == params.membership_plan
#         )

#     if params.search_key:
#         search_pattern = f"%{params.search_key}%"
#         query = query.filter(
#             or_(
#                 _models.Client.wallet_address.ilike(search_pattern),
#                 _models.Client.profile_img.ilike(search_pattern),
#                 _models.Client.own_member_id.ilike(search_pattern),
#                 _models.Client.first_name.ilike(search_pattern),
#                 _models.Client.last_name.ilike(search_pattern),
#                 _models.Client.gender.ilike(search_pattern),
#                 _models.Client.email.ilike(search_pattern),
#                 _models.Client.phone.ilike(search_pattern),
#                 _models.Client.mobile_number.ilike(search_pattern),
#                 _models.Client.notes.ilike(search_pattern),
#                 _models.Client.language.ilike(search_pattern),
#                 _models.Client.city.ilike(search_pattern),
#                 _models.Client.zipcode.ilike(search_pattern),
#                 _models.Client.address_1.ilike(search_pattern),
#                 _models.Client.address_2.ilike(search_pattern),
#             )
#         )

#     # Add order by created_at and limit/offset for pagination
#     query = query.order_by(sort_order).offset(params.offset).limit(params.limit)
#     clients = query.all()
#     print(clients)
#     return [
#         _schemas.ClientFilterRead(
#             id=client.id,
#             own_member_id=client.own_member_id,
#             first_name=client.first_name,
#             last_name=client.last_name,
#             phone=client.phone,
#             mobile_number=client.mobile_number,
#             check_in=client.check_in,
#             last_online=client.last_online,
#             client_since=client.client_since,
#             business_name=client.business_name,
#             coach_name=client.coach_name,
#         )
#         for client in clients
#     ]


def get_filtered_clients(
    db: _orm.Session,
    org_id: int,
    params: _schemas.ClientFilterParams
) -> List[_schemas.ClientFilterRead]:
    BusinessClient = _orm.aliased(_models.Client) 
    sort_mapping = {

        "own_member_id": text("client.own_member_id"),
        "first_name": text("client.first_name"),
        "last_name": text("client.last_name"),
        "business_name": "business_name",
        "last_online": text("client.last_online"),
        "client_since": text("client.client_since"),
        "created_at": text("client.created_at"),
        "client_status": text("client_organization.client_status"),
        "membership_plan_id":text("client_membership.membership_plan_id")                      
    }

    query = db.query(
        *_models.Client.__table__.columns,
        _models.ClientOrganization.org_id,
        _models.ClientOrganization.client_status,
        _models.ClientMembership.membership_plan_id,
        func.array_agg(
            func.json_build_object(
                'id',func.coalesce(_models.ClientCoach.coach_id, 0),
                'coach_name', func.concat(
                    func.coalesce(_coach_models.Coach.first_name, ""),
                    ' ',
                    func.coalesce(_coach_models.Coach.last_name, "")
                ))).label('coaches'),
        func.coalesce(BusinessClient.first_name + ' ' + BusinessClient.last_name, _models.Client.first_name + ' ' + _models.Client.last_name).label('business_name'))\
    .outerjoin(
        BusinessClient, _models.Client.business_id == BusinessClient.id
    ).outerjoin(
        _models.ClientCoach,and_(_models.Client.id == _models.ClientCoach.client_id,_models.ClientCoach.is_deleted == False)
    ).outerjoin(
        _coach_models.Coach,and_(_coach_models.Coach.id == _models.ClientCoach.coach_id,_coach_models.Coach.is_deleted == False)
    ).join(
        _models.ClientOrganization, _models.Client.id == _models.ClientOrganization.client_id
    ).join(
        _models.ClientMembership, _models.Client.id == _models.ClientMembership.client_id
    ).filter(
        _models.Client.is_deleted == False,
        _models.ClientOrganization.org_id == org_id
    ).group_by(
        _models.Client.id,
        _models.ClientOrganization.id,
        _models.ClientMembership.membership_plan_id,
        BusinessClient.id
    )
    
    total_counts = db.query(func.count()).select_from(query.subquery()).scalar()

    if params.member_name:
        query = query.filter(or_(
            _models.Client.first_name.ilike(f"%{params.member_name}%"),
            _models.Client.last_name.ilike(f"%{params.member_name}%")
        ))

    if params.status:
        query = query.filter(_models.ClientOrganization.client_status == params.status)
    
    if params.coach_assigned:
        query = query.filter(_models.ClientCoach.coach_id == params.coach_assigned)

    if params.membership_plan:
        query = query.filter(
            _models.ClientMembership.membership_plan_id == params.membership_plan)

    if params.search_key:
        search_pattern = f"%{params.search_key}%"
        query = query.filter(
            or_(
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
                _models.Client.address_2.ilike(search_pattern),
            )
        )
    
    filtered_counts = db.query(func.count()).select_from(query.subquery()).scalar()

    if params.sort_key in sort_mapping.keys():
        sort_order = desc(sort_mapping.get(params.sort_key)) if params.sort_order == "desc" else asc(sort_mapping.get(params.sort_key))
        query = query.order_by(sort_order)

    elif params.sort_key is not None:
        raise _fastapi.HTTPException(status_code=400, detail="Sorting column not found.")
    
    query = query.offset(params.offset).limit(params.limit)
    db_clients = query.all()

    clients = []
    for client in db_clients:
        clients.append(_schemas.ClientFilterRead(**client._asdict()))

    return {"data": clients, "total_counts": total_counts, "filtered_counts": filtered_counts}
   


async def get_client_byid(db: _orm.Session, client_id: int) -> _schemas.ClientByID:
    query = db.query(
            *_models.Client.__table__.columns,
            _models.ClientOrganization.org_id,
            _models.ClientMembership.membership_plan_id,
            func.array_agg(
            func.json_build_object(
                'id', func.coalesce(_models.ClientCoach.coach_id, 0),
                'name', func.concat(
                    func.coalesce(_coach_models.Coach.first_name, ""), 
                    ' ', 
                    func.coalesce(_coach_models.Coach.last_name, "")
                )
            )
        ).label('coaches')
        ).outerjoin(
            _models.ClientCoach, _models.Client.id == _models.ClientCoach.client_id
        ).outerjoin(
            _coach_models.Coach, _coach_models.Coach.id == _models.ClientCoach.coach_id
        ).join(
            _models.ClientOrganization, _models.Client.id == _models.ClientOrganization.client_id
        ).join(
            _models.ClientMembership, _models.Client.id == _models.ClientMembership.client_id
        ).filter(
            _models.Client.id == client_id,
            _models.Client.is_deleted == False
        ).group_by(
            _models.Client.id,
            _models.ClientOrganization.org_id,
            _models.ClientMembership.membership_plan_id
        )
    

    db_client=query.first()

    if db_client:
        return _schemas.ClientByID(**db_client._asdict())
    else:
        return None
    
