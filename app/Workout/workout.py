import sqlalchemy.orm as _orm

from fastapi import APIRouter, Depends
from app.core.db import session as _database


router = APIRouter(tags=["Workout router"])

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class WorkoutController:
    def __init__(self, db_session: _orm.Session = Depends(get_db)):
        self.db = db_session


