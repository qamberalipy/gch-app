
import datetime 
import jwt
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  ,desc
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

def update_credit(credit_update: _schemas.CreditUpdate, db: _orm.Session):
    db_credit = db.query(_models.Credits).filter(_models.Credits.id == credit_update.id).first()
    if not db_credit:
        return None

    if credit_update.name is not None:
        db_credit.name = credit_update.name
    if credit_update.org_id is not None:
        db_credit.org_id = credit_update.org_id
    if credit_update.min_limit is not None:
        db_credit.min_limit = credit_update.min_limit
    if credit_update.status is not None:
        db_credit.status = credit_update.status
    if credit_update.updated_by is not None:
        db_credit.updated_by = credit_update.updated_by

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
    return db.query(_models.Credits).filter(_models.Credits.org_id == org_id, _models.Credits.is_deleted == False).order_by(desc(_models.Credits.created_at)).all()

def get_credit_by_id(credit_id: int,db: _orm.Session):
    return db.query(_models.Credits).filter(_models.Credits.id == credit_id, _models.Credits.is_deleted == False).first()

def create_income_category(income_category: _schemas.IncomeCategoryCreate, db: _orm.Session):
    db_income_category = _models.Income_category(**income_category.dict())
    db.add(db_income_category)
    db.commit()
    db.refresh(db_income_category)
    return db_income_category

def get_all_income_categories_by_org_id(org_id: int, db: _orm.Session):
    return db.query(_models.Income_category).filter(_models.Income_category.org_id == org_id, _models.Income_category.is_deleted == False).order_by(desc(_models.Income_category.created_at)).all()

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

def get_all_sale_taxes_by_org_id(org_id: int,db: _orm.Session):
    return db.query(_models.Sale_tax).filter(_models.Sale_tax.org_id == org_id, _models.Sale_tax.is_deleted == False).order_by(desc(_models.Sale_tax.created_at)).all()


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