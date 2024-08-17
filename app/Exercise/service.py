from typing import Annotated, Optional
from sqlalchemy import and_, asc, desc, func, inspect, or_, select, text
import sqlalchemy.orm as _orm
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.Exercise.models as _models
import app.Exercise.schema as _schemas
from datetime import datetime
from sqlalchemy.orm import aliased
from app.Exercise.models import VisibleFor,ExerciseType,Difficulty

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


async def get_met(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.MET.__table__.columns)

async def get_category(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.ExerciseCategory.__table__.columns)

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
        exercise_intensity=exercise.exercise_intensity,
        intensity_value=exercise.intensity_value,
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

    return {"status":"201","detail":"Exercise updated successfully"}   

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


async def get_equipments(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.Equipment.__table__.columns)

async def get_primary_joints(db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(*_models.PrimaryJoint.__table__.columns)

def get_filters(

    search_key: Annotated[str, _fastapi.Query(title="Search Key")] = None,
    category: Annotated[list[int] , _fastapi.Query(title="Category")] = None,
    visible_for:Annotated[list[VisibleFor], _fastapi.Query(title="Visible For")] = None,
    difficulty:Annotated[Difficulty, _fastapi.Query(title="Visible For")] = None,
    exercise_type:Annotated[ExerciseType, _fastapi.Query(title="Visible For")] = None,
    sort_key:Annotated[str, _fastapi.Query(title="Sort Key")] = None,
    sort_order:Annotated[str, _fastapi.Query(title="Sort Order")] = 'desc',
    limit: Annotated[int, _fastapi.Query(description="Pagination Limit")] = None,
    offset: Annotated[int, _fastapi.Query(description="Pagination offset")] = None
):
    return _schemas.ExerciseFilterParams(
        search_key=search_key,
        category=category,
        visible_for=visible_for,
        exercise_type=exercise_type,
        difficulty=difficulty,
        sort_key=sort_key,
        sort_order=sort_order,
        limit=limit,
        offset = offset
    )

async def delete_exercise(id:int,db: _orm.Session = _fastapi.Depends(get_db)):
    db_exercise=db.query(_models.Exercise).filter(and_(_models.Exercise.id==id,_models.Exercise.is_deleted==False)).first()

    if db_exercise:
        db_exercise.is_deleted = True
        db.commit()    
    else :
        raise _fastapi.HTTPException(status_code=404, detail="Exercise not found")

    return {"detail": "Exercise deleted successfully"}

def extract_columns(query):
    columns = []
    if hasattr(query.statement, 'columns'):
        columns = [col.name for col in query.statement.columns]
    return columns


async def get_exercise(
    params: Optional[_schemas.ExerciseFilterParams] = None,
    org_id: Optional[int] = None,
    id: Optional[int] = None,
    db: _orm.Session = _fastapi.Depends(get_db)
):
    sort_mapping = {
        "exercise_name": text("filtered_exercise.exercise_name"),
        "category_name": text("exercise_category.category_name"),
        "visible_for": text("filtered_exercise.visible_for"),
        "created_at": text("filtered_exercise.created_at"),
        "difficulty":text("filtered_exercise.difficulty"),
        "exercise_type":text("filtered_exercise.exercise_type"),
        "set":text("filtered_exercise.sets")
    }
    
    PrimaryMuscle = aliased(_models.Muscle)
    SecondaryMuscle = aliased(_models.Muscle)
    PrimaryJoint = aliased(_models.PrimaryJoint)
    Equipment = aliased(_models.Equipment)
    Exercise = aliased(_models.Exercise)
    
    if id:
        check_exercise = db.query(Exercise).filter(Exercise.id == id).first()
        if not check_exercise:
            raise _fastapi.HTTPException(status_code=400, detail="Exercise Not Found")  
    
    if org_id:
        check_organization = db.query(Exercise.org_id).filter(Exercise.org_id == org_id).first()
        if not check_organization:
            raise _fastapi.HTTPException(status_code=400, detail="Organization Not Found")
 
    query = db.query(Exercise).filter(Exercise.is_deleted == False)


    equipment_query = db.query(
        _models.ExerciseEquipment.exercise_id,
        func.json_agg(
            func.json_build_object('id', Equipment.id, 'name', Equipment.equipment_name)
        ).label('equipments')
    ).join(
        Equipment, _models.ExerciseEquipment.equipment_id == Equipment.id
    ).group_by(_models.ExerciseEquipment.exercise_id).subquery()

    primary_muscle_query = db.query(
        _models.ExercisePrimaryMuscle.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(PrimaryMuscle.id, 0), 'name', func.coalesce(PrimaryMuscle.muscle_name, ""))
        ).label('primary_muscles')
    ).join(
        PrimaryMuscle, _models.ExercisePrimaryMuscle.muscle_id == PrimaryMuscle.id
    ).group_by(_models.ExercisePrimaryMuscle.exercise_id).subquery()

    secondary_muscle_query = db.query(
        _models.ExerciseSecondaryMuscle.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(SecondaryMuscle.id, 0), 'name', func.coalesce(SecondaryMuscle.muscle_name, ""))
        ).label('secondary_muscles')
    ).join(
        SecondaryMuscle, _models.ExerciseSecondaryMuscle.muscle_id == SecondaryMuscle.id
    ).group_by(_models.ExerciseSecondaryMuscle.exercise_id).subquery()

    primary_joint_query = db.query(
        _models.ExercisePrimaryJoint.exercise_id,
        func.json_agg(
            func.json_build_object('id', func.coalesce(PrimaryJoint.id, 0), 'name', func.coalesce(PrimaryJoint.joint_name, ""))
        ).label('primary_joints')
    ).join(
        PrimaryJoint, _models.ExercisePrimaryJoint.primary_joint_id == PrimaryJoint.id
    ).group_by(_models.ExercisePrimaryJoint.exercise_id).subquery()

    if params:
       
        if params.search_key:
            search_pattern = f"%{params.search_key}%"
            query = query.filter(Exercise.exercise_name.ilike(search_pattern))

        if params.category:
            query = query.filter(Exercise.category_id.in_(params.category))    

        if params.difficulty:
            query = query.filter(Exercise.difficulty == params.difficulty)

        if params.visible_for:
            query=query.filter(Exercise.visible_for.in_(params.visible_for)) 

        if params.exercise_type:
            query = query.filter(Exercise.exercise_type == params.exercise_type)      

        query = query.filter(Exercise.org_id == org_id)     

        
    filtered_exercise_query = query.subquery('filtered_exercise')
    
    query = db.query(
        filtered_exercise_query.c.exercise_name,
        filtered_exercise_query.c.visible_for,
        filtered_exercise_query.c.org_id,
        filtered_exercise_query.c.exercise_type,
        filtered_exercise_query.c.exercise_intensity,
        filtered_exercise_query.c.intensity_value,
        filtered_exercise_query.c.difficulty,
        filtered_exercise_query.c.sets,
        filtered_exercise_query.c.seconds_per_set,
        filtered_exercise_query.c.repetitions_per_set,
        filtered_exercise_query.c.rest_between_set,
        filtered_exercise_query.c.distance,
        filtered_exercise_query.c.speed,
        filtered_exercise_query.c.met_id,
        filtered_exercise_query.c.gif_url,
        filtered_exercise_query.c.video_url_male,
        filtered_exercise_query.c.video_url_female,
        filtered_exercise_query.c.thumbnail_male,
        filtered_exercise_query.c.thumbnail_female,
        filtered_exercise_query.c.image_url_female,
        filtered_exercise_query.c.image_url_male,
        filtered_exercise_query.c.id,
        filtered_exercise_query.c.category_id,
        filtered_exercise_query.c.created_at,
        _models.ExerciseCategory.category_name,
        equipment_query.c.equipments,
        primary_muscle_query.c.primary_muscles,
        secondary_muscle_query.c.secondary_muscles,
        primary_joint_query.c.primary_joints
    ).join(
        equipment_query, filtered_exercise_query.c.id == equipment_query.c.exercise_id
    ).join(
        _models.ExerciseCategory, filtered_exercise_query.c.category_id == _models.ExerciseCategory.id
    ).join(
        primary_muscle_query, filtered_exercise_query.c.id == primary_muscle_query.c.exercise_id
    ).join(
        secondary_muscle_query, filtered_exercise_query.c.id == secondary_muscle_query.c.exercise_id
    ).join(
        primary_joint_query, filtered_exercise_query.c.id == primary_joint_query.c.exercise_id
    )
 
    if id:
        query = query.filter(filtered_exercise_query.c.id == id)
        return query.first()

    total_count_query = db.query(Exercise.id).filter(and_(Exercise.is_deleted == False,Exercise.org_id == org_id))
    total_counts = db.query(func.count()).select_from(total_count_query.subquery()).scalar()
    
    filtered_counts = db.query(func.count()).select_from(query.subquery()).scalar()

    if params.sort_key in sort_mapping.keys():
        sort_order = desc(sort_mapping.get(params.sort_key)) if params.sort_order == "desc" else asc(sort_mapping.get(params.sort_key))
        query = query.order_by(sort_order)
    elif params.sort_key is not None:
        raise _fastapi.HTTPException(status_code=400, detail="Sorting column not found.")
    
    query = query.offset(params.offset).limit(params.limit)
    
    db_exercise = query.all()
    exercise_data = [_schemas.ExerciseRead.from_orm(exercise) for exercise in db_exercise]
    return {'data': exercise_data, 'total_counts': total_counts, 'filtered_counts': filtered_counts}


        
    
    
    







