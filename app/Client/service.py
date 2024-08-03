from datetime import date
import datetime
import string
from typing import List
import jwt
from pydantic import ValidationError
from sqlalchemy import asc, desc, func, or_
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
    org_id: int,
    email_address: str,
    wallet_address: str,
    db: _orm.Session = _fastapi.Depends(get_db),
) -> dict:
    client = (
        db.query(models.Client, _models.ClientOrganization)
        .join(
            _models.ClientOrganization,
            and_(_models.Client.id == _models.ClientOrganization.client_id,
            _models.ClientOrganization.org_id == org_id,)
        )
        .filter(
            _models.Client.email == email_address, _models.Client.is_deleted == False
        )
        .first()
    )

    if not client:
        return {"is_registered": False}

    client = client[0]
    client.wallet_address = wallet_address
    db.commit()
    db.refresh(client)
    

    token = _helpers.create_token(dict(id=client.id, org_id=org_id), "Member")

    return {"is_registered": True, "client": client, "access_token": token}


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
    db_client = db.query(_models.Client).filter(_models.Client.id == client_id).first()
    if not db_client:
        raise _fastapi.HTTPException(status_code=404, detail="Client not found")
    client.is_deleted = False
    for key, value in client.dict(exclude_unset=True).items():
        setattr(db_client, key, value)

    db_client.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_client)
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


async def delete_client(client_id: int, db: _orm.Session = _fastapi.Depends(get_db)):
    db_client = db.query(_models.Client).filter(_models.Client.id == client_id).first()
    if not db_client:
        raise _fastapi.HTTPException(status_code=404, detail="Client not found")

    db_client.is_deleted = True
    db_client.updated_at = datetime.datetime.now()
    db.commit()
    db.refresh(db_client)
    return db_client


def get_list_clients(
    org_id: int, db: _orm.Session = _fastapi.Depends(get_db)
) -> List[models.Client]:
    return (
        db.query(_models.Client.id, _models.Client.first_name, _models.Client.last_name)
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


def get_filtered_clients(
    db: _orm.Session,
    org_id:int,
    params: _schemas.ClientFilterParams

) -> List[_schemas.ClientFilterRead]:
    # Create a base query with the necessary joins
    query = db.query(
        _models.Client.id,
        _models.Client.own_member_id,
        _models.Client.first_name,
        _models.Client.last_name,
        _models.Client.phone,
        _models.Client.mobile_number,
        _models.Client.check_in,
        _models.Client.last_online,
        _models.Client.client_since,
        func.coalesce(
            _models.Client.first_name,
            db.query(_models.Client.first_name).filter(_models.Client.id == _models.Client.business_id)
        ).label("business_name"),
        _coach_models.Coach.first_name.label("coach_name")
    ).join(
        _models.ClientOrganization, _models.Client.id == _models.ClientOrganization.client_id
    ).join(
        _models.ClientCoach, _models.Client.id == _models.ClientCoach.client_id
    ).join(
        _models.ClientMembership, _models.Client.id == _models.ClientMembership.client_id
    ).join(
        _coach_models.Coach, _models.ClientCoach.coach_id == _coach_models.Coach.id
    ).filter(
        _models.ClientOrganization.org_id == org_id,
        _models.ClientOrganization.is_deleted == False,
        _models.Client.is_deleted==False,
        _coach_models.Coach.is_deleted == False
    )

    sort_order = (
        desc(_models.Client.created_at)
        if params.sort_order == "desc"
        else asc(_models.Client.created_at)
    )

    # Apply filters conditionally

    if params.member_name:
        query = query.filter(or_(
            _models.Client.first_name.ilike(f"%{params.member_name}%"),
            _models.Client.last_name.ilike(f"%{params.member_name}%")
        ))

    if params.status:
        query = query.filter(
            _models.ClientOrganization.client_status.ilike(f"%{params.status}%")
        )

    if params.coach_assigned:
        query = query.filter(_models.ClientCoach.coach_id == params.coach_assigned)

    if params.membership_plan:
        query = query.filter(
            _models.ClientMembership.membership_plan_id == params.membership_plan
        )

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

    # Add order by created_at and limit/offset for pagination
    query = query.order_by(sort_order).offset(params.offset).limit(params.limit)
    clients = query.all()
    print(clients)
    return [
        _schemas.ClientFilterRead(
            id=client.id,
            own_member_id=client.own_member_id,
            first_name=client.first_name,
            last_name=client.last_name,
            phone=client.phone,
            mobile_number=client.mobile_number,
            check_in=client.check_in,
            last_online=client.last_online,
            client_since=client.client_since,
            business_name=client.business_name,
            coach_name=client.coach_name,
        )
        for client in clients
    ]


async def get_client_byid(db: _orm.Session, client_id: int) -> _schemas.ClientByID:
    query = (
        db.query(
            _models.Client.id,
            _models.Client.wallet_address,
            _models.Client.profile_img,
            _models.Client.own_member_id,
            _models.Client.first_name,
            _models.Client.last_name,
            _models.Client.gender,
            _models.Client.dob,
            _models.Client.email,
            _models.Client.phone,
            _models.Client.mobile_number,
            _models.Client.notes,
            _models.Client.source_id,
            _models.Client.language,
            _models.Client.is_business,
            _models.Client.business_id,
            _models.Client.country_id,
            _models.Client.city,
            _models.Client.zipcode,
            _models.Client.address_1,
            _models.Client.address_2,
            _models.Client.height,
            _models.Client.weight,
            _models.Client.bmi,
            _models.Client.circumference_waist_navel,
            _models.Client.fat_percentage,
            _models.Client.muscle_percentage,
            _models.Client.activated_on,
            _models.Client.check_in,
            _models.Client.last_online,
            _models.Client.client_since,
            _models.Client.created_at,
            _models.Client.updated_at,
            _models.Client.created_by,
            _models.Client.updated_by,
            _models.Client.is_deleted,
            _models.ClientOrganization.org_id,
            _models.ClientMembership.membership_plan_id,
        )
        .join(_models.ClientCoach, _models.Client.id == _models.ClientCoach.client_id)
        .join(_models.ClientOrganization, _models.Client.id == _models.ClientOrganization.client_id)
        .join(_models.ClientMembership, _models.Client.id == _models.ClientMembership.client_id)
        .filter(_models.Client.id == client_id,
                _models.Client.is_deleted == False
            )
    )

    result = query.first()
    if not result:
        return None

    business_name = None
    if result.is_business and result.business_id:
        business_client = (
            db.query(_models.Client)
            .filter(_models.Client.id == result.business_id)
            .first()
        )
        if business_client:
            business_name = business_client.first_name

    coaches = db.query(
    _models.ClientCoach.coach_id,
        func.concat(_coach_models.Coach.first_name, ' ', _coach_models.Coach.last_name).label("coach_name")
    ).join(
        _coach_models.Coach, _coach_models.Coach.id == _models.ClientCoach.coach_id
    ).filter(
        _models.ClientCoach.client_id == client_id
    ).all()

    coach_list = [{"coach_id": coach.coach_id, "coach_name": coach.coach_name} for coach in coaches]

    return _schemas.ClientByID(
        id=result.id,
        wallet_address=result.wallet_address,
        profile_img=result.profile_img,
        own_member_id=result.own_member_id,
        first_name=result.first_name,
        last_name=result.last_name,
        gender=result.gender,
        dob=result.dob,
        email=result.email,
        phone=result.phone,
        mobile_number=result.mobile_number,
        notes=result.notes,
        source_id=result.source_id,
        language=result.language,
        is_business=result.is_business,
        business_id=result.business_id,
        country_id=result.country_id,
        city=result.city,
        zipcode=result.zipcode,
        address_1=result.address_1,
        address_2=result.address_2,
        height=result.height,
        weight=result.weight,
        bmi=result.bmi,
        circumference_waist_navel=result.circumference_waist_navel,
        fat_percentage=result.fat_percentage,
        muscle_percentage=result.muscle_percentage,
        activated_on=result.activated_on,
        check_in=result.check_in,
        last_online=result.last_online,
        client_since=result.client_since,
        created_at=result.created_at,
        updated_at=result.updated_at,
        created_by=result.created_by,
        updated_by=result.updated_by,
        is_deleted=result.is_deleted,
        business_name=business_name,
        coach_id=coach_list,
        org_id=result.org_id,
        membership_plan_id=result.membership_plan_id
    )
