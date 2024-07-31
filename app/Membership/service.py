import datetime
import jwt
import sqlalchemy.orm as _orm
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
from sqlalchemy.sql import and_  ,desc
from fastapi import FastAPI, Header,APIRouter, Depends, HTTPException, Request, status
from . import models, schema
from typing import List 
from sqlalchemy import asc, text

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
        
        
def create_membership_plan(membership_plan: _schemas.MembershipPlanCreate, db: _orm.Session):
    
    existing_plan = db.query(models.MembershipPlan).filter(
        models.MembershipPlan.name == membership_plan.name,
        models.MembershipPlan.org_id == membership_plan.org_id
    ).first()
    
    if existing_plan:
        raise HTTPException(status_code=400,detail=f"Membership plan already exists.")
        
    db_membership_plan = models.MembershipPlan(
        name=membership_plan.name,
        org_id=membership_plan.org_id,
        group_id=membership_plan.group_id,
        status=membership_plan.status,
        description=membership_plan.description,
        access_time=membership_plan.access_time,
        net_price=membership_plan.net_price,
        income_category_id=membership_plan.income_category_id,
        discount=membership_plan.discount,
        total_price=membership_plan.total_price,
        payment_method=membership_plan.payment_method,
        reg_fee=membership_plan.reg_fee,
        billing_cycle=membership_plan.billing_cycle,
        auto_renewal=membership_plan.auto_renewal,
        renewal_details=membership_plan.renewal_details,
        created_by=membership_plan.created_by,
    )
    db.add(db_membership_plan)
    db.commit()
    db.refresh(db_membership_plan)

    for facility in membership_plan.facilities:
        db_facility_membership_plan = models.Facility_membership_plan(
            facility_id=facility.id,
            membership_plan_id=db_membership_plan.id,
            total_credits=facility.total_credits,
            validity=facility.validity,
        )
        db.add(db_facility_membership_plan)

    db.commit()
    return db_membership_plan

def update_facility_membership_plans(membership_plan_id: int, facilities: List[_schemas.FacilityMembershipPlan], db: _orm.Session):
    for facility_data in facilities:
        db_facility_membership_plan = db.query(models.Facility_membership_plan).filter(
            models.Facility_membership_plan.membership_plan_id == membership_plan_id,
            models.Facility_membership_plan.facility_id == facility_data.id
        ).first()

        if not db_facility_membership_plan:
            # Create a new facility membership plan if it doesn't exist
            new_facility_membership_plan = models.Facility_membership_plan(
                membership_plan_id=membership_plan_id,
                facility_id=facility_data.id,
                total_credits=facility_data.total_credits,
                validity=facility_data.validity
            )
            db.add(new_facility_membership_plan)
        else:
            # Update the existing facility membership plan
            if facility_data.total_credits is not None:
                db_facility_membership_plan.total_credits = facility_data.total_credits
            if facility_data.validity is not None:
                db_facility_membership_plan.validity = facility_data.validity

    db.commit()

def update_membership_plan(membership_plan_id: int, membership_plan: _schemas.MembershipPlanUpdate, db: _orm.Session):
    db_membership_plan = db.query(models.MembershipPlan).filter(models.MembershipPlan.id == membership_plan_id).first()
    if not db_membership_plan:
        return None  # Return None if the membership plan does not exist

    # Update only the fields that are provided
    update_data = membership_plan.dict(exclude_unset=True, exclude={"facilities"})
    for key, value in update_data.items():
        setattr(db_membership_plan, key, value)

    db.commit()
    db.refresh(db_membership_plan)

    # Update facilities if provided
    if membership_plan.facilities:
        update_facility_membership_plans(membership_plan_id, membership_plan.facilities, db)

    return db_membership_plan



def delete_membership_plan( membership_plan_id: int,db: _orm.Session):
    db_membership_plan = db.query(models.MembershipPlan).filter(models.MembershipPlan.id == membership_plan_id).first()
    if db_membership_plan:
        db_membership_plan.is_deleted = True
        db.commit()
        db.refresh(db_membership_plan)
    return db_membership_plan

def get_membership_plan_by_id(membership_plan_id: int, db: _orm.Session):
    membership_plan = db.query(models.MembershipPlan).filter(
        models.MembershipPlan.id == membership_plan_id, 
        models.MembershipPlan.is_deleted == False
    ).first()
    
    if membership_plan is None:
        raise _fastapi.HTTPException(status_code=404, detail="Membership plan not found")
    
    facilities = db.query(models.Facility_membership_plan).filter(
        models.Facility_membership_plan.membership_plan_id == membership_plan_id, 
        models.Facility_membership_plan.is_deleted == False
    ).all()

    facility_responses = [
        _schemas.FacilityMembershipPlan(
            id=facility.id,
            total_credits=facility.total_credits,
            validity=facility.validity
        ) for facility in facilities
    ]

    response = _schemas.MembershipPlanResponse(
        name=membership_plan.name,
        org_id=membership_plan.org_id,
        group_id=membership_plan.group_id,
        status=membership_plan.status,
        description=membership_plan.description,
        access_time=membership_plan.access_time,
        net_price=membership_plan.net_price,
        income_category_id=membership_plan.income_category_id,
        discount=membership_plan.discount,
        total_price=membership_plan.total_price,
        payment_method=membership_plan.payment_method,
        reg_fee=membership_plan.reg_fee,
        billing_cycle=membership_plan.billing_cycle,
        auto_renewal=membership_plan.auto_renewal,
        renewal_details=membership_plan.renewal_details,
        facilities=facility_responses,
        created_by=membership_plan.created_by
    )

    return response

def get_membership_plans_by_org_id(
    db: _orm.Session,
    parameters: _schemas.MembershipFilterParams
):
    filters = ["mp.org_id = :org_id", "mp.is_deleted = False"]
    params = {"org_id": parameters.org_id}

    if parameters.group_id is not None:
        filters.append("mp.group_id = :group_id")
        params["group_id"] = parameters.group_id

    if parameters.income_category_id is not None:
        filters.append("mp.income_category_id = :income_category_id")
        params["income_category_id"] = parameters.income_category_id

    if parameters.discount_percentage is not None:
        filters.append("mp.discount = :discount_percentage")
        params["discount_percentage"] = parameters.discount_percentage

    if parameters.total_amount is not None:
        filters.append("mp.total_price = :total_amount")
        params["total_amount"] = parameters.total_amount

    if parameters.status is not None:
        filters.append("mp.status = :status")
        params["status"] = parameters.status

    if parameters.search_key is not None:
        filters.append("mp.name ILIKE :name")
        params["name"] = f"%{parameters.search_key}%"

    sort_order = "ASC" if parameters.sort_order.lower() == "asc" else "DESC"

    query = text(f"""
        SELECT 
            mp.id,
            mp.name,
            mp.org_id,
            mp.group_id,
            mp.status,
            mp.description,
            mp.access_time,
            mp.net_price,
            mp.income_category_id,
            mp.discount,
            mp.total_price,
            mp.payment_method,
            mp.reg_fee,
            mp.billing_cycle,
            mp.auto_renewal,
            mp.renewal_details,
            mp.created_by,
            mp.created_at,
            json_agg(
                json_build_object(
                    'id', COALESCE(f.id, 0),
                    'total_credits', COALESCE(fmp.total_credits, 0),
                    'validity', fmp.validity
                )
            ) AS facilities
        FROM membership_plan mp
        LEFT JOIN facility_membership_plan fmp ON fmp.membership_plan_id = mp.id
        LEFT JOIN facility f ON f.id = fmp.facility_id
        WHERE {" AND ".join(filters)}
        GROUP BY 
            mp.id, mp.name, mp.org_id, mp.group_id, mp.status, 
            mp.description, CAST(mp.access_time AS text), mp.net_price, 
            mp.income_category_id, mp.discount, mp.total_price, mp.payment_method,
            mp.reg_fee, mp.billing_cycle, mp.auto_renewal, CAST(mp.renewal_details AS text), mp.created_by, mp.created_at
        ORDER BY mp.created_at {sort_order}
        LIMIT :limit OFFSET :offset;
    """)

    params["limit"] = parameters.limit
    params["offset"] = parameters.offset

    result = db.execute(query, params)
    return result.fetchall()


def create_facility(facility: _schemas.FacilityCreate,db: _orm.Session):
    
    existing_facility = db.query(_models.Facility
    ).filter(_models.Facility.name == facility.name, _models.Facility.org_id == facility.org_id).first()
    
    if existing_facility:
        raise HTTPException(status_code=400, detail="Facility with this name already exists.")
    
    db_facility = _models.Facility(
        name=facility.name,
        org_id=facility.org_id,
        min_limit=facility.min_limit,
        created_by=facility.created_by
    )
    db.add(db_facility)
    db.commit()
    db.refresh(db_facility)
    return db_facility

def update_facility(facility_update: _schemas.FacilityUpdate, db: _orm.Session):
    db_facility = db.query(_models.Facility).filter(_models.Facility.id == facility_update.id).first()
    if not db_facility:
        return None

    if facility_update.name is not None:
        db_facility.name = facility_update.name
    if facility_update.org_id is not None:
        db_facility.org_id = facility_update.org_id
    if facility_update.min_limit is not None:
        db_facility.min_limit = facility_update.min_limit
    if facility_update.status is not None:
        db_facility.status = facility_update.status
    if facility_update.updated_by is not None:
        db_facility.updated_by = facility_update.updated_by

    db.commit()
    db.refresh(db_facility)
    return db_facility


def delete_facility( facility_id: int,db: _orm.Session):
    db_facility = db.query(_models.Facility).filter(_models.Facility.id == facility_id).first()
    if not db_facility:
        return None
    
    db_facility.is_deleted = True
    db.commit()
    return db_facility

def get_facility_by_org_id(db: _orm.Session, params: _schemas.StandardParams):
    sort_order = desc(_models.Facility.created_at) if params.sort_order == "desc" else asc(_models.Facility.created_at)
    
    facilities_query = db.query(_models.Facility)\
        .filter(_models.Facility.org_id == params.org_id, _models.Facility.is_deleted == False)\
        .order_by(sort_order)\
        .offset(params.offset)\
        .limit(params.limit)
    
    return facilities_query.all()

def get_facility_by_id(facility_id: int,db: _orm.Session):
    return db.query(_models.Facility).filter(_models.Facility.id == facility_id, _models.Facility.is_deleted == False).first()

def create_income_category(income_category: _schemas.IncomeCategoryCreate, db: _orm.Session):
    db_income_category = _models.Income_category(**income_category.dict())
    db.add(db_income_category)
    db.commit()
    db.refresh(db_income_category)
    return db_income_category

def get_all_income_categories_by_org_id(db: _orm.Session, params: _schemas.StandardParams):
    sort_order = desc(_models.Income_category.created_at) if params.sort_order == "desc" else asc(_models.Income_category.created_at)
    
    income_categories_query = db.query(_models.Income_category)\
        .filter(_models.Income_category.org_id == params.org_id, _models.Income_category.is_deleted == False)\
        .order_by(sort_order)\
        .offset(params.offset)\
        .limit(params.limit)
    
    return income_categories_query.all()

def get_income_category_by_id(income_category_id: int, db: _orm.Session):
    return db.query(_models.Income_category).filter(_models.Income_category.id == income_category_id, _models.Income_category.is_deleted == False).first()

def update_income_category(income_category: _schemas.IncomeCategoryUpdate, db: _orm.Session):
    db_income_category = db.query(_models.Income_category).filter(_models.Income_category.id == income_category.id).first()
    if not db_income_category:
        return None

    if income_category.name is not None:
        db_income_category.name = income_category.name
    if income_category.position is not None:
        db_income_category.position = income_category.position
    if income_category.sale_tax_id is not None:
        db_income_category.sale_tax_id = income_category.sale_tax_id
    if income_category.org_id is not None:
        db_income_category.org_id = income_category.org_id
    if income_category.updated_by is not None:
        db_income_category.updated_by = income_category.updated_by

    db_income_category.updated_at = datetime.datetime.now()

    db.commit()
    db.refresh(db_income_category)
    return db_income_category

def delete_income_category(income_category_id: int, db: _orm.Session):
    db_income_category = db.query(_models.Income_category).filter(_models.Income_category.id == income_category_id).first()
    if db_income_category is None:
        return None
    db_income_category.is_deleted = True
    db_income_category.updated_at = datetime.datetime.now()
    db.commit()
    db.refresh(db_income_category)
    return db_income_category

def create_sale_tax(sale_tax: _schemas.SaleTaxCreate,db: _orm.Session):
    db_sale_tax = _models.Sale_tax(**sale_tax.dict())
    db.add(db_sale_tax)
    db.commit()
    db.refresh(db_sale_tax)
    return db_sale_tax

def get_all_sale_taxes_by_org_id(db: _orm.Session, params: _schemas.StandardParams):
    sort_order = desc(_models.Sale_tax.created_at) if params.sort_order == "desc" else asc(_models.Sale_tax.created_at)
    
    sale_taxes_query = db.query(_models.Sale_tax)\
        .filter(_models.Sale_tax.org_id == params.org_id, _models.Sale_tax.is_deleted == False)\
        .order_by(sort_order)\
        .offset(params.offset)\
        .limit(params.limit)
    
    return sale_taxes_query.all()


def get_sale_tax_by_id(sale_tax_id: int,db: _orm.Session):
    return db.query(_models.Sale_tax).filter(_models.Sale_tax.id == sale_tax_id, _models.Sale_tax.is_deleted == False).first()


def update_sale_tax(sale_tax: _schemas.SaleTaxUpdate, db: _orm.Session):
    db_sale_tax = db.query(_models.Sale_tax).filter(_models.Sale_tax.id == sale_tax.id).first()
    if not db_sale_tax:
        return None

    if sale_tax.name is not None:
        db_sale_tax.name = sale_tax.name
    if sale_tax.percentage is not None:
        db_sale_tax.percentage = sale_tax.percentage
    if sale_tax.org_id is not None:
        db_sale_tax.org_id = sale_tax.org_id
    if sale_tax.updated_by is not None:
        db_sale_tax.updated_by = sale_tax.updated_by

    db_sale_tax.updated_at = datetime.datetime.now()

    db.commit()
    db.refresh(db_sale_tax)
    return db_sale_tax


def delete_sale_tax(sale_tax_id: int,db: _orm.Session):
    db_sale_tax = db.query(_models.Sale_tax).filter(_models.Sale_tax.id == sale_tax_id).first()
    if db_sale_tax is None:
        return None
    db_sale_tax.is_deleted = True
    db_sale_tax.updated_at = datetime.datetime.now()
    db.commit()
    db.refresh(db_sale_tax)
    return db_sale_tax


def create_group(group: _schemas.GroupCreate,db: _orm.Session):
    db_group = _models.Membership_group(**group.model_dump())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

def get_group_by_id(id:int,db: _orm.Session):
    
    return db.query(_models.Membership_group).filter(_models.Membership_group.id == id, _models.Membership_group.is_deleted == False).first()


def get_all_groups_by_org_id(db: _orm.Session, params: _schemas.StandardParams):
    sort_order = desc(_models.Membership_group.created_at) if params.sort_order == "desc" else asc(_models.Membership_group.created_at)
    
    groups_query = db.query(_models.Membership_group)\
        .filter(_models.Membership_group.org_id == params.org_id, _models.Membership_group.is_deleted == False)\
        .order_by(sort_order)\
        .offset(params.offset)\
        .limit(params.limit)
    
    return groups_query.all()


def update_group(group:_schemas.GroupUpdate,db:_orm.Session):
    db_group = db.query(_models.Membership_group).filter(_models.Membership_group.id == group.id).first()
    
    if not db_group:
        return None
    
    if group.name is not None:
        db_group.name = group.name

    db_group.updated_at = datetime.datetime.now()
    db.commit()
    db.refresh(db_group)
    return db_group    
    
    
