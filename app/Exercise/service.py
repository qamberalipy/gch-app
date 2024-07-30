from sqlalchemy import and_, desc, func, or_
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
        org_id=exercise.org_id,
        category_id=exercise.category_id,
        exercise_type=exercise.exercise_type,
        difficulty=exercise.difficulty,
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

    
async def get_exercise(org_id:int,db: _orm.Session = _fastapi.Depends(get_db)):

    Exercise = aliased(_models.Exercise)
    PrimaryMuscle = aliased(_models.Muscle)
    SecondaryMuscle = aliased(_models.Muscle)
    PrimaryJoint = aliased(_models.PrimaryJoint)
    Equipment = aliased(_models.Equipment)


    equipment_query = db.query(
        _models.ExerciseEquipment.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(Equipment.id,0), 'name', func.coalesce(Equipment.equipment_name,""))
        ).label('equipments')
    ).join(
        Equipment, _models.ExerciseEquipment.equipment_id == Equipment.id
    ).group_by(_models.ExerciseEquipment.exercise_id).subquery()
    

    primary_muscle_query = db.query(
        _models.ExercisePrimaryMuscle.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(PrimaryMuscle.id,0), 'name', func.coalesce(PrimaryMuscle.muscle_name,""))
        ).label('primary_muscles')
    ).join(
        PrimaryMuscle, _models.ExercisePrimaryMuscle.muscle_id == PrimaryMuscle.id
    ).group_by(_models.ExercisePrimaryMuscle.exercise_id).subquery()


    secondary_muscle_query = db.query(
       _models.ExerciseSecondaryMuscle.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(SecondaryMuscle.id,0), 'name', func.coalesce(SecondaryMuscle.muscle_name,""))
        ).label('secondary_muscles')
    ).join(
        SecondaryMuscle, _models.ExerciseSecondaryMuscle.muscle_id == SecondaryMuscle.id
    ).group_by( _models.ExerciseSecondaryMuscle.exercise_id).subquery()


    primary_joint_query = db.query(
         _models.ExercisePrimaryJoint.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(PrimaryJoint.id,0), 'name', func.coalesce(PrimaryJoint.joint_name,""))
        ).label('primary_joints')
    ).join(
        PrimaryJoint, _models.ExercisePrimaryJoint.primary_joint_id == PrimaryJoint.id
    ).group_by(_models.ExercisePrimaryJoint.exercise_id).subquery()

    query = db.query(
    Exercise.exercise_name,
    Exercise.visible_for,
    Exercise.org_id,
    Exercise.category_id,
    Exercise.exercise_type,
    Exercise.difficulty,
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
    equipment_query.c.equipments,
    primary_muscle_query.c.primary_muscles,
    secondary_muscle_query.c.secondary_muscles,
    primary_joint_query.c.primary_joints
    ).select_from(Exercise).join(
    equipment_query, Exercise.id == equipment_query.c.exercise_id
    ).join(
    primary_muscle_query, Exercise.id == primary_muscle_query.c.exercise_id
    ).join(
    secondary_muscle_query, Exercise.id == secondary_muscle_query.c.exercise_id
    ).join(
    primary_joint_query, Exercise.id == primary_joint_query.c.exercise_id).filter(
    Exercise.is_deleted == False and Exercise.org_id==org_id
    ).all()

    return query



async def get_exercise_by_id(id:int,db: _orm.Session = _fastapi.Depends(get_db)):

    Exercise = aliased(_models.Exercise)
    PrimaryMuscle = aliased(_models.Muscle)
    SecondaryMuscle = aliased(_models.Muscle)
    PrimaryJoint = aliased(_models.PrimaryJoint)
    Equipment = aliased(_models.Equipment)

    equipment_query = db.query(
        _models.ExerciseEquipment.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(Equipment.id,0), 'name', func.coalesce(Equipment.equipment_name,""))
        ).label('equipments')
    ).join(
        Equipment,and_(_models.ExerciseEquipment.equipment_id == Equipment.id,_models.ExerciseEquipment.exercise_id==id)
    ).group_by(_models.ExerciseEquipment.exercise_id).subquery()
    

    primary_muscle_query = db.query(
        _models.ExercisePrimaryMuscle.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(PrimaryMuscle.id,0), 'name', func.coalesce(PrimaryMuscle.muscle_name,""))
        ).label('primary_muscles')
    ).join(
        PrimaryMuscle, and_(_models.ExercisePrimaryMuscle.muscle_id == PrimaryMuscle.id, _models.ExercisePrimaryMuscle.exercise_id==id)
    ).group_by(_models.ExercisePrimaryMuscle.exercise_id).subquery()


    secondary_muscle_query = db.query(
       _models.ExerciseSecondaryMuscle.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(SecondaryMuscle.id,0), 'name', func.coalesce(SecondaryMuscle.muscle_name,""))
        ).label('secondary_muscles')
    ).join(
        SecondaryMuscle,and_(_models.ExerciseSecondaryMuscle.muscle_id == SecondaryMuscle.id,_models.ExerciseSecondaryMuscle.exercise_id==id)
    ).group_by( _models.ExerciseSecondaryMuscle.exercise_id).subquery() 


    primary_joint_query = db.query(
         _models.ExercisePrimaryJoint.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(PrimaryJoint.id,0), 'name', func.coalesce(PrimaryJoint.joint_name,""))
        ).label('primary_joints')
    ).join(
        PrimaryJoint,and_(_models.ExercisePrimaryJoint.primary_joint_id == PrimaryJoint.id,_models.ExercisePrimaryJoint.exercise_id==id)
    ).group_by(_models.ExercisePrimaryJoint.exercise_id).subquery()

    query = db.query(
    Exercise.exercise_name,
    Exercise.visible_for,
    Exercise.org_id,
    Exercise.category_id,
    Exercise.exercise_type,
    Exercise.difficulty,
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
    equipment_query.c.equipments,
    primary_muscle_query.c.primary_muscles,
    secondary_muscle_query.c.secondary_muscles,
    primary_joint_query.c.primary_joints
    ).select_from(Exercise).join(
    equipment_query, Exercise.id == equipment_query.c.exercise_id
    ).join(
    primary_muscle_query, Exercise.id == primary_muscle_query.c.exercise_id
    ).join(
    secondary_muscle_query, Exercise.id == secondary_muscle_query.c.exercise_id
    ).join(
    primary_joint_query, Exercise.id == primary_joint_query.c.exercise_id).filter(
    Exercise.is_deleted == False 
    ).first()

    return query

async def get_equipments(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.Equipment.__table__.columns)

async def get_primary_joints(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.PrimaryJoint.__table__.columns)
