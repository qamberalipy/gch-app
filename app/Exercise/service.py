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

    existing_exercise = db.query(_models.Exercise).filter(
        _models.Exercise.exercise_name == exercise.exercise_name,
        _models.Exercise.org_id == exercise.org_id
    ).first()

    if existing_exercise:
        raise _fastapi.HTTPException(status_code=400, detail="Exercise with the same name already exists in the organization.")
    
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
        updated_by=exercise.updated_by)
    
    db.add(db_exercise)
    db.commit()

    equipments=create_exercise_equipment(db_exercise.id,exercise.equipment_ids,db)
    primary_muscles=create_exercise_primary_muscle(db_exercise.id,exercise.primary_muscle_ids,db)
    primary_joints=create_exercise_primary_joint(db_exercise.id,exercise.primary_joint_ids,db)
    secondary_muscles=create_exercise_secondary_muscle(db_exercise.id,exercise.secondary_muscle_ids,db)

    db.add_all(equipments + primary_muscles + primary_joints + secondary_muscles) 
    db.commit()   
    
    return db_exercise.id


def create_exercise_equipment(exercise_id,equipment_ids,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise_equipment=[_models.ExerciseEquipment(
    exercise_id=exercise_id,
    equipment_id=equipment_id    
    )for equipment_id in equipment_ids]    

    return db_exercise_equipment 

def create_exercise_primary_muscle(exercise_id,primary_muscle_ids,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise_primary_muscle=[_models.ExercisePrimaryMuscle(
    exercise_id=exercise_id,
    muscle_id=primary_muscle_id    
    )for primary_muscle_id in primary_muscle_ids]    
    
    return db_exercise_primary_muscle

async def exercise_update(data:_schemas.ExerciseUpdate,db: _orm.Session = _fastapi.Depends(get_db)):
    data_update=[]
    db_exercise=db.query(_models.Exercise).filter(_models.Exercise.id==data.id).first()
    if db_exercise:
        for key, value in data.dict(exclude_unset=True).items():
            setattr(db_exercise, key, value)
        db.commit()
        db.refresh(db_exercise)

    query1=db.query(_models.ExerciseEquipment).filter(_models.ExerciseEquipment.exercise_id==data.id).all()
    query2=db.query(_models.ExercisePrimaryMuscle).filter(_models.ExercisePrimaryMuscle.exercise_id==data.id).all()
    query3=db.query(_models.ExercisePrimaryJoint).filter(_models.ExercisePrimaryJoint.exercise_id==data.id).all()
    query4=db.query(_models.ExerciseSecondaryMuscle).filter(_models.ExerciseSecondaryMuscle.exercise_id==data.id).all()

    delete_equipment_ids = [item.equipment_id for item in query1]
    delete_primary_muscle_ids=[item.muscle_id for item in query2]
    delete_secondary_muscle_ids=[item.primary_joint_id for item in query3]
    delete_primary_joint_ids=[item.muscle_id for item in query4]

    add_equipment_ids=data.equipment_ids
    add_primary_muscle_ids=data.primary_muscle_ids
    add_primary_joint_ids=data.primary_joint_ids
    add_secondary_muscle_ids=data.secondary_muscle_ids

    for equipment_id in delete_equipment_ids:
        if equipment_id in add_equipment_ids:
            delete_equipment_ids.remove(equipment_id)
            add_equipment_ids.remove(equipment_id)

    for muscle_id in delete_primary_muscle_ids:
        if muscle_id in add_primary_muscle_ids:
            delete_primary_muscle_ids.remove(muscle_id)
            add_primary_muscle_ids.remove(muscle_id)

    for muscle_id in delete_secondary_muscle_ids:
        if muscle_id in add_secondary_muscle_ids:
            delete_secondary_muscle_ids.remove(muscle_id)
            add_secondary_muscle_ids.remove(muscle_id)

    for joint_id in delete_primary_joint_ids:
        if joint_id in add_primary_joint_ids:
            delete_primary_joint_ids.remove(joint_id)
            add_primary_joint_ids.remove(joint_id)

    if add_equipment_ids:
        equipments=create_exercise_equipment(data.id,add_equipment_ids,db)
    
    if add_primary_muscle_ids:
        primary_muscles=create_exercise_primary_muscle(data.id,add_primary_muscle_ids,db)   
    
    if add_secondary_muscle_ids:
        secondary_muscles=create_exercise_secondary_muscle(data.id,add_secondary_muscle_ids,db)  
        data_update.append(secondary_muscles) 
    
    if add_primary_joint_ids:
        primary_joints=create_exercise_primary_joint(data.id,add_primary_joint_ids,db)   
   
    db.add_all(equipments + primary_muscles + secondary_muscles + primary_joints) 
    
    if delete_equipment_ids:
        delete_exercise_data(data.id,equipment_ids=delete_equipment_ids,db=db)

    if delete_primary_muscle_ids:
        delete_exercise_data(data.id,primary_muscle_ids=delete_primary_muscle_ids,db=db)

    if delete_secondary_muscle_ids:
        delete_exercise_data(data.id,secondary_muscle_ids=delete_secondary_muscle_ids,db=db)

    if delete_primary_joint_ids:
        delete_exercise_data(data.id,primary_joint_ids=delete_primary_joint_ids,db=db)   

    db.commit()

    return data    

def create_exercise_primary_joint(exercise_id,primary_joint_ids,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise_primary_joint=[_models.ExercisePrimaryJoint(
    exercise_id=exercise_id,
    primary_joint_id=primary_joint_id    
    )for primary_joint_id in primary_joint_ids]    
    
    return db_exercise_primary_joint

def create_exercise_secondary_muscle(exercise_id,secondary_muscle_ids,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise_secondary_muscle=[_models.ExerciseSecondaryMuscle(
    exercise_id=exercise_id,
    muscle_id=secondary_muscle_id   
    )for secondary_muscle_id in secondary_muscle_ids]    
    
    return db_exercise_secondary_muscle

    
async def get_exercise(org_id:int,db: _orm.Session = _fastapi.Depends(get_db)):

    Exercise = aliased(_models.Exercise)
    PrimaryMuscle = aliased(_models.Muscle)
    SecondaryMuscle = aliased(_models.Muscle)
    PrimaryJoint = aliased(_models.PrimaryJoint)
    Equipment = aliased(_models.Equipment)


    equipment_query = db.query(
        _models.ExerciseEquipment.exercise_id,
        func.json_agg(
            func.json_build_object('id',Equipment.id, 'name',Equipment.equipment_name)
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
    Exercise.is_deleted == False and Exercise.org_id==org_id).all()
    print("this is query",query)
    return query


def delete_exercise_data(exercise_id:int,equipment_ids:list[int]=None,primary_muscle_ids:list[int]=None,
secondary_muscle_ids:list[int]=None,primary_joint_ids:list[int]=None,db: _orm.Session = _fastapi.Depends(get_db)):
    
    if equipment_ids:
        db.query(_models.ExerciseEquipment).filter(
        _models.ExerciseEquipment.exercise_id == exercise_id,
       _models.ExerciseEquipment.equipment_id.in_(equipment_ids)
       ).delete(synchronize_session=False)

    if primary_muscle_ids:
        db.query(_models.ExercisePrimaryMuscle).filter(
        _models.ExercisePrimaryMuscle.exercise_id == exercise_id,
       _models.ExercisePrimaryMuscle.muscle_id.in_(primary_muscle_ids)
       ).delete(synchronize_session=False)

    if secondary_muscle_ids:
        db.query(_models.ExerciseSecondaryMuscle).filter(
        _models.ExerciseSecondaryMuscle.exercise_id == exercise_id,
       _models.ExerciseSecondaryMuscle.muscle_id.in_(secondary_muscle_ids)
       ).delete(synchronize_session=False)    

    if primary_joint_ids:
        db.query(_models.ExercisePrimaryJoint).filter(
        _models.ExercisePrimaryJoint.exercise_id == exercise_id,
       _models.ExercisePrimaryJoint.primary_joint_id.in_(primary_joint_ids)
       ).delete(synchronize_session=False)    


async def get_exercise_by_id(id:int,db: _orm.Session = _fastapi.Depends(get_db)):

    Exercise = aliased(_models.Exercise)
    PrimaryMuscle = aliased(_models.Muscle)
    SecondaryMuscle = aliased(_models.Muscle)
    PrimaryJoint = aliased(_models.PrimaryJoint)
    Equipment = aliased(_models.Equipment)

    check_exercise=db.query(_models.Exercise).filter(_models.Exercise.id==id)
    if not check_exercise:
        raise _fastapi.HTTPException(status_code=404, detail="Exercise not found")

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
    Exercise.is_deleted == False).first()

    print("this is queyr",query)

    return query


async def get_equipments(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.Equipment.__table__.columns)

async def get_primary_joints(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.PrimaryJoint.__table__.columns)
