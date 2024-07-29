from sqlalchemy import desc, func, or_
import sqlalchemy.orm as _orm
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Exercise.models as _models
import app.Exercise.schema as _schemas

def create_database():
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_muscle(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.Muscle.__table__.columns)

async def create_exercise(exercise:_schemas.ExerciseCreate,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise = _models.Exercise(**exercise.dict())
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise
