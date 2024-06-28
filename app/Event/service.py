from datetime import date
import jwt
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Event.schema as _schemas
import app.Event.models as _models
import random
import json
import time
import os
import bcrypt as _bcrypt

# Load environment variables
# JWT_SECRET = os.getenv("JWT_SECRET")

def read_all_events(db: _orm.Session):
    return db.query(_models.Events).all()


def read_event_by_id(event_id: int, db: _orm.Session):
    return db.query(_models.Events).filter(_models.Events.id == event_id).first()


def create_event(event: _schemas.EventCreate, db: _orm.Session):
    db_event = _models.Events(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def update_event(event_id: int, event: _schemas.EventUpdate, db: _orm.Session):
    db_event = db.query(_models.Events).filter(_models.Events.id == event_id).first()
    for key, value in event.dict().items():
        setattr(db_event, key, value)
    db.commit()
    db.refresh(db_event)
    return db_event