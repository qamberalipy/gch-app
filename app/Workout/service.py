from typing import List, Literal
from fastapi import Depends, HTTPException
from sqlalchemy import Column, update
from sqlalchemy.orm import Session, joinedload, selectinload
from starlette.types import HTTPExceptionHandler

from app.Workout import workout
from .models import Workout, WorkoutDay, WorkoutDayExercise
from ..Shared.schema import PaginationOptions
from .schema import (
    WorkoutCreate,
    WorkoutDayCreate,
    WorkoutDayExerciseCreate,
    WorkoutDayExerciseFilter,
    WorkoutDayExerciseRead,
    WorkoutDayExerciseUpdate,
    WorkoutDayFilter,
    WorkoutDayRead,
    WorkoutDayUpdate,
    WorkoutFilter,
    WorkoutRead,
    WorkoutUpdate,
)


async def update_workout(
    db: Session, workout_model: Workout, workout: WorkoutUpdate, user_id: int
):
    model = workout_model
    data = workout.model_dump(exclude_unset=True)
    data["updated_by"] = user_id
    for key, value in data.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model


async def delete_workout(
    db: Session, workout_id: int, workout_model: Workout, user_id: int
):
    model = workout_model
    setattr(model, "is_deleted", True)
    setattr(model, "updated_by", user_id)
    db.commit()
    db.refresh(model)
    return model


async def update_workout_day(
    db: Session,
    workout_day_model: WorkoutDay,
    workout_day: WorkoutDayUpdate,
    user_id: int,
):
    model = workout_day_model
    data = workout_day.model_dump(exclude_unset=True)
    data["updated_by"] = user_id
    for key, value in data.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model


async def delete_workout_day(
    db: Session, workout_day_id: int, workout_day_model: WorkoutDay, user_id: int
):
    model = workout_day_model
    setattr(model, "is_deleted", True)
    setattr(model, "updated_by", user_id)
    db.execute(
        update(WorkoutDayExercise)
        .where(WorkoutDayExercise.workout_day_id == workout_day_id)
        .values(is_deleted=True)
    )
    db.commit()
    db.refresh(model)
    return model


async def update_workout_day_exercise(
    db: Session,
    workout_day_exercise_model: WorkoutDayExercise,
    workout_day_exercise: WorkoutDayExerciseUpdate,
    user_id: int,
):
    model = workout_day_exercise_model
    data = workout_day_exercise.model_dump(exclude_unset=True)
    data["updated_by"] = user_id
    for key, value in data.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model


async def delete_workout_day_exercise(
    db: Session, workout_day_exercise_model: WorkoutDayExercise, user_id: int
):
    model = workout_day_exercise_model
    setattr(model, "is_deleted", True)
    setattr(model, "updated_by", user_id)
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


async def get_workout(
    db: Session,
    workout_id: int,
    include_days: bool = False,
    include_days_and_exercises: bool = False,
):
    exclude_by_default = {"days"}

    query = db.query(Workout).filter(
        Workout.id == workout_id, Workout.is_deleted == False
    )

    if include_days:
        query = query.options(joinedload(Workout.days))
        exclude_by_default = {"days": {"__all__": {"exercises"}}}

    if include_days_and_exercises:
        query = query.options(joinedload(Workout.days).joinedload(WorkoutDay.exercises))
        exclude_by_default = {}

    return WorkoutRead.model_validate(query.first()).model_dump(
        exclude=exclude_by_default
    )


async def get_all_workout(
    db: Session, params: WorkoutFilter, pagination_options: PaginationOptions
):
    exclude_by_default = {"days"}
    query = db.query(Workout).filter(Workout.is_deleted == False)
    if params.goals:
        query = query.filter(Workout.goals == params.goals)
    if params.level:
        query = query.filter(Workout.level == params.level)
    if params.search:
        query = query.filter(Workout.workout_name.ilike(f"%{params.search}%"))
    if params.include_days:
        query = query.options(joinedload(Workout.days))
        exclude_by_default.remove("days")
    if params.include_days:
        query = query.options(joinedload(Workout.days))
        exclude_by_default = {"days": {"__all__": {"exercises"}}}
    if pagination_options.offset:
        query = query.offset(pagination_options.offset)
    if pagination_options.limit:
        query = query.limit(pagination_options.limit)

    if params.include_days_and_exercises:
        query = query.options(joinedload(Workout.days).joinedload(WorkoutDay.exercises))
        exclude_by_default = {}
    return [
        WorkoutRead.model_validate(item).model_dump(exclude=exclude_by_default)
        for item in query.all()
    ]


async def get_workout_day(
    db: Session, workout_day_id: int, include_exercises: bool = False
):
    exclude_by_default = {"exercises"}
    query = db.query(WorkoutDay).filter(
        WorkoutDay.id == workout_day_id, WorkoutDay.is_deleted == False
    )
    if include_exercises:
        query = query.options(joinedload(WorkoutDay.exercises))
        exclude_by_default = {}
    return WorkoutDayRead.model_validate(query.first()).model_dump(
        exclude=exclude_by_default
    )


async def get_all_workout_day(
    db: Session, params: WorkoutDayFilter, pagination_options: PaginationOptions
):
    exclude_by_default = {"exercises"}
    query = db.query(WorkoutDay).filter(WorkoutDay.is_deleted == False)
    if params.workout_id:
        query = query.filter(WorkoutDay.workout_id == params.workout_id)
    if params.week:
        query = query.filter(WorkoutDay.week == params.week)
    if params.day:
        query = query.filter(WorkoutDay.day == params.day)
    if params.include_exercises:
        query = query.options(joinedload(WorkoutDay.exercises))
        exclude_by_default = {}
    if pagination_options.offset:
        query = query.offset(pagination_options.offset)
    if pagination_options.limit:
        query = query.limit(pagination_options.limit)
    return [
        WorkoutDayRead.model_validate(item).model_dump(exclude=exclude_by_default)
        for item in query.all()
    ]


async def save_workout_day(db: Session, workout: WorkoutDayCreate, user_id: int):
    data = workout.model_dump()
    data["created_by"] = user_id
    db_workout_day = WorkoutDay(**data)
    db.add(db_workout_day)
    db.commit()
    db.refresh(db_workout_day)
    return db_workout_day


async def save_workout_day_exercise(
    db: Session, workout_day_exercise: WorkoutDayExerciseCreate, user_id: int
):
    data = workout_day_exercise.model_dump()
    data["created_by"] = user_id
    db_workout_day_exercise = WorkoutDayExercise(**data)
    db.add(db_workout_day_exercise)
    db.commit()
    db.refresh(db_workout_day_exercise)
    return db_workout_day_exercise


async def get_all_workout_day_exercise(
        db: Session, params: WorkoutDayExerciseFilter, pagination_options: PaginationOptions
) -> List[WorkoutDayExerciseRead]:
    query = db.query(WorkoutDayExercise).filter(WorkoutDayExercise.is_deleted == False)
    if params.workout_day_id:
        query = query.filter(WorkoutDayExercise.workout_day_id == params.workout_day_id)
    if pagination_options.offset:
        query = query.offset(pagination_options.offset)
    if pagination_options.limit:
        query = query.limit(pagination_options.limit)
    return [WorkoutDayExerciseRead.model_validate(item) for item in query.all()]


async def get_workout_day_exercise(
    db: Session, workout_day_exercise_id: int
) -> WorkoutDayExerciseRead:
    return (
        db.query(WorkoutDayExercise)
        .filter(
            WorkoutDayExercise.id == workout_day_exercise_id,
            WorkoutDayExercise.is_deleted == False,
        )
        .first()
    )
