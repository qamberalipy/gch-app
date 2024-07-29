from typing import Literal
from fastapi import Depends, HTTPException
from sqlalchemy import Column
from sqlalchemy.orm import Session
from starlette.types import HTTPExceptionHandler

from app.Workout import workout
from .models import Workout, WorkoutDay, WorkoutDayExercise
from .schema import WorkoutCreate, WorkoutDayCreate, WorkoutDayExerciseCreate, WorkoutDayExerciseRead, WorkoutDayExerciseUpdate, WorkoutDayFilter, WorkoutDayRead, WorkoutDayUpdate, WorkoutFilter, WorkoutRead, WorkoutUpdate

async def update_workout(db: Session, workout_id: int, workout: WorkoutUpdate, user_id: int):
    model = db.query(Workout).filter(Workout.id == workout_id, Workout.is_deleted == False).first()
    if not model:
        raise HTTPException(status_code=404, detail="Workout doesn't exist")
    data = workout.model_dump(exclude_unset=True)
    data["updated_by"] = user_id
    for key, value in data.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model

async def update_workout_day(db: Session, workout_day_model: WorkoutDay, workout_day: WorkoutDayUpdate, user_id: int):
    model = workout_day_model
    data = workout_day.model_dump(exclude_unset=True)
    data["updated_by"] = user_id
    for key, value in data.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model

async def update_workout_day_exercise(db: Session, workout_day_exercise_model: WorkoutDayExercise, 
                                      workout_day_exercise: WorkoutDayExerciseUpdate, user_id: int):
    model = workout_day_exercise_model
    data = workout_day_exercise.model_dump(exclude_unset=True)
    data["updated_by"] = user_id
    for key, value in data.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model

async def save_workout(db: Session, workout: WorkoutCreate, user_id: int):
    data = workout.model_dump()
    data["created_by"] = user_id
    db_workout = Workout(**data)
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout

async def get_workout(db: Session, workout_id: int) -> WorkoutRead:
    return db.query(Workout).filter(Workout.id == workout_id, Workout.is_deleted == False).first()  

async def get_all_workout(db: Session, params: WorkoutFilter):
    query = db.query(Workout).filter(Workout.is_deleted == False)
    if params.goals:
        query = query.filter(Workout.goals == params.goals)
    if params.level:
        query = query.filter(Workout.level == params.level)
    if params.search:
        query = query.filter(Workout.workout_name.ilike(f"%{params.search}%"))
    return query.all()


async def get_workout_day(db: Session, workout_day_id: int) -> WorkoutDayRead:
    return db.query(WorkoutDay).filter(WorkoutDay.id == workout_day_id, WorkoutDay.is_deleted == False).first()

async def get_all_workout_day(db: Session, params: WorkoutDayFilter):
    query = db.query(WorkoutDay).filter(WorkoutDay.is_deleted == False)
    if params.week:
        query = query.filter(WorkoutDay.week == params.week)
    if params.day:
        query = query.filter(WorkoutDay.day == params.day)
    return [WorkoutDayRead.model_validate(item, from_attributes=True) for item in query.all()]

async def save_workout_day(db: Session, workout: WorkoutDayCreate, user_id: int):
    data = workout.model_dump()
    data["created_by"] = user_id
    db_workout_day = WorkoutDay(**data)
    db.add(db_workout_day)
    db.commit()
    db.refresh(db_workout_day)
    return db_workout_day

async def save_workout_day_exercise(db: Session, workout_day_exercise: WorkoutDayExerciseCreate, user_id: int):
    data = workout_day_exercise.model_dump()
    data["created_by"] = user_id
    db_workout_day_exercise = WorkoutDayExercise(**data)
    db.add(db_workout_day_exercise)
    db.commit()
    db.refresh(db_workout_day_exercise)
    return db_workout_day_exercise

async def get_workout_day_exercise(db: Session, workout_day_exercise_id: int) -> WorkoutDayExerciseRead:
    return db.query(WorkoutDay).filter(WorkoutDay.id == workout_day_exercise_id, WorkoutDay.is_deleted == False).first()
