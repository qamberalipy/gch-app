from sqlalchemy import desc, func, or_
import sqlalchemy.orm as _orm
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Exercise.models as _models
import app.Exercise.schema as _schemas
from datetime import datetime
from sqlalchemy.orm import aliased

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

async def create_exercise(exercise: _schemas.ExerciseCreate, db: _orm.Session):
    db_exercise = _models.Exercise(
        exercise_name=exercise.exercise_name,
        visible_for=exercise.visible_for,
        category_id=exercise.category_id,
        exercise_type=exercise.exercise_type,
        sets=exercise.sets,
        seconds_per_set=exercise.seconds_per_set,
        repetitions_per_set=exercise.repetitions_per_set,
        rest_between_set=exercise.rest_between_set,
        distance=exercise.distance,
        speed=exercise.speed,
        met_id=exercise.met_id,
        gif_url=exercise.gif_url,
        video_url_male=exercise.video_url_male,
        video_url_female=exercise.video_url_female,
        thumbnail_male=exercise.thumbnail_male,
        thumbnail_female=exercise.thumbnail_female,
        image_url_female=exercise.image_url_female,
        image_url_male=exercise.image_url_male,
        created_by=exercise.created_by,
        updated_by=exercise.updated_by)
    
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)

    create_exercise_equipment(db_exercise.id,exercise.equipment_ids,db)
    create_exercise_primary_muscle(db_exercise.id,exercise.primary_muscle_ids,db)
    create_exercise_primary_joint(db_exercise.id,exercise.primary_joint_ids,db)
    create_exercise_secondary_muscle(db_exercise.id,exercise.secondary_muscle_ids,db)

    return db_exercise


def create_exercise_equipment(exercise_id,equipment_ids,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise_equipment=[_models.ExerciseEquipment(
    exercise_id=exercise_id,
    equipment_id=equipment_id    
    )for equipment_id in equipment_ids]    
    
    db.add_all(db_exercise_equipment)
    db.commit()

    for new_exercise_equipment in db_exercise_equipment:
        db.refresh(new_exercise_equipment) 

def create_exercise_primary_muscle(exercise_id,primary_muscle_ids,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise_primary_muscle=[_models.ExercisePrimaryMuscle(
    exercise_id=exercise_id,
    muscle_id=primary_muscle_id    
    )for primary_muscle_id in primary_muscle_ids]    
    
    db.add_all(db_exercise_primary_muscle)
    db.commit()

    for new_exercise_primary_muscle in db_exercise_primary_muscle:
        db.refresh(new_exercise_primary_muscle)  


def create_exercise_primary_joint(exercise_id,primary_joint_ids,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise_primary_joint=[_models.ExercisePrimaryJoint(
    exercise_id=exercise_id,
    primary_joint_id=primary_joint_id    
    )for primary_joint_id in primary_joint_ids]    
    
    db.add_all(db_exercise_primary_joint)
    db.commit()

    for new_exercise_primary_joint in db_exercise_primary_joint:
        db.refresh(new_exercise_primary_joint)  


def create_exercise_secondary_muscle(exercise_id,secondary_muscle_ids,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise_secondary_muscle=[_models.ExerciseSecondaryMuscle(
    exercise_id=exercise_id,
    muscle_id=secondary_muscle_id   
    )for secondary_muscle_id in secondary_muscle_ids]    
    
    db.add_all(db_exercise_secondary_muscle)
    db.commit()

    for new_exercise_secondary_muscle in db_exercise_secondary_muscle:
        db.refresh(new_exercise_secondary_muscle)

    
async def get_exercise(db: _orm.Session = _fastapi.Depends(get_db)):

    Exercise = aliased(_models.Exercise)
    PrimaryMuscle = aliased(_models.Muscle)
    SecondaryMuscle = aliased(_models.Muscle)
    PrimaryJoint = aliased(_models.PrimaryJoint)
    Equipment = aliased(_models.Equipment)

    query = db.query(
        Exercise.exercise_name,
        Exercise.visible_for,
        Exercise.category_id,
        Exercise.exercise_type,
        Exercise.sets,
        Exercise.seconds_per_set,
        Exercise.repetitions_per_set,
        Exercise.rest_between_set,
        Exercise.distance,
        Exercise.speed,
        Exercise.met_id,
        Exercise.gif_url,
        Exercise.video_url_male,
        Exercise.video_url_female,
        Exercise.thumbnail_male,
        Exercise.thumbnail_female,
        Exercise.image_url_female,
        Exercise.image_url_male,
        Exercise.id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(Equipment.id,0), 'name', func.coalesce(Equipment.equipment_name,""))
        ).label('equipments')
    ).select_from(
        Exercise
    ).join(
        _models.ExerciseEquipment, Exercise.id == _models.ExerciseEquipment.exercise_id
    ).join(
        Equipment, _models.ExerciseEquipment.equipment_id == Equipment.id
    ).filter(
        Exercise.is_deleted == False
    ).group_by(Exercise.id).all()

    print(query)

    return query


async def get_equipments(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.Equipment.__table__.columns)

async def get_primary_joints(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.PrimaryJoint.__table__.columns)







