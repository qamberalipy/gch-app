from operator import and_
from typing import Annotated, List, Literal, Union
from fastapi import Depends, HTTPException
from sqlalchemy import Column, asc, desc, distinct, func, or_, update
from sqlalchemy.orm import Query, Session, joinedload, selectinload
from starlette.types import HTTPExceptionHandler

from app.Shared.dependencies import get_user
from app.Exercise.models import Exercise, ExerciseEquipment
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
    WorkoutMobileFilter,
    WorkoutRead,
    WorkoutUpdate,
)


async def update_workout(
    db: Session, workout_model: Workout, workout: WorkoutUpdate, user: dict
):
    model = workout_model
    data = workout.model_dump(exclude_unset=True)
    data["updated_by"] = user["id"]
    data["update_user_type"] = user["user_type"]
    for key, value in data.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return model


async def delete_workout(db: Session, workout_model: Workout, user_id: int):
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


async def save_workout(db: Session, user: dict, workout: WorkoutCreate):
    data = workout.model_dump()
    data["org_id"] = user["org_id"]
    data["create_user_type"] = user["user_type"]
    data["created_by"] = user["id"]
    db_workout = Workout(**data)
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout


async def get_workout(
    db: Session,
    org_id: int,
    workout_id: int,
):
    query = db.query(Workout).filter(
        Workout.id == workout_id, Workout.is_deleted == False, Workout.org_id == org_id
    )
    return query.first()


async def get_workout_filter(
    db: Session,
    user: dict,
    workout_id: int,
    org_id: int,
    include_days: bool = False,
    include_days_and_exercises: bool = False,
):
    id, user_type, org_id = user["id"], user["user_type"], user["org_id"]
    exclude_by_default = {"days"}

    query = db.query(Workout).filter(
        Workout.id == workout_id,
        Workout.is_deleted == False,
        Workout.org_id == org_id,
    )

    if include_days:
        query = query.options(joinedload(Workout.days))
        exclude_by_default = {"days": {"__all__": {"exercises"}}}

    if include_days_and_exercises:
        query = query.options(
            joinedload(Workout.days)
            .joinedload(WorkoutDay.exercises)
            .joinedload(WorkoutDayExercise.exercise)
        )
        exclude_by_default = {}

    if user_type == "member" or user_type == "coach":
        query = query.filter(
            or_(
                Workout.visible_for == "everyone_in_my_club",
                Workout.visible_for == "members_in_my_club",
                and_(
                    Workout.visible_for == "only_myself",
                    (Workout.created_by == id)
                    & (Workout.create_user_type == user_type),
                ),
            ).self_group()
        )

    workout = query.first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return WorkoutRead.model_validate(workout).model_dump(exclude=exclude_by_default)

    workout = query.first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return WorkoutRead.model_validate(workout).model_dump(exclude=exclude_by_default)

def _workout_get_count_before_pagination(
    db: Session, user: dict, params: WorkoutFilter
):
    id, user_type, org_id = user["id"], user["user_type"], user["org_id"]
    query = db.query(func.count(distinct(Workout.id))).filter(
        Workout.is_deleted == False, Workout.org_id == org_id
    )
    if user_type == "member" or user_type == "coach":
        query = query.filter(
            or_(
                Workout.visible_for == "everyone_in_my_club",
                Workout.visible_for == "members_of_my_club",
                and_(
                    Workout.visible_for == "only_myself",
                    (Workout.created_by == id)
                    & (Workout.create_user_type == user_type),
                ).self_group(),
            ).self_group()
        )
    if params.goals:
        query = query.filter(Workout.goals == params.goals)
    if params.level:
        query = query.filter(Workout.level == params.level)
    if params.search:
        query = query.filter(Workout.workout_name.ilike(f"%{params.search}%"))
    if params.created_by_user:
        query = query.filter(
            Workout.create_user_type == user_type, Workout.created_by == id
        )
    if params.include_days_and_exercises:
        query = query.options(joinedload(Workout.days).joinedload(WorkoutDay.exercises))
    if params.equipment_id:
        query = (
            query.join(WorkoutDay, WorkoutDay.workout_id == Workout.id)
            .join(
                WorkoutDayExercise, WorkoutDayExercise.workout_day_id == WorkoutDay.id
            )
            .join(Exercise, Exercise.id == WorkoutDayExercise.exercise_id)
            .join(ExerciseEquipment, ExerciseEquipment.exercise_id == Exercise.id)
            .filter(ExerciseEquipment.equipment_id == params.equipment_id)
        )
    return query.scalar()


def _extract_columns(query):
    columns = []
    if hasattr(query.statement, "columns"):
        columns = [col.name for col in query.statement.columns]
    return columns


def workout_apply_filter(query, params: Union[WorkoutFilter,WorkoutMobileFilter], exclude_by_default, user: dict):
    user_type = user["user_type"]
    if user_type == "member" or user_type == "coach":
        query = query.filter(
            or_(
                Workout.visible_for == "everyone_in_my_club",
                Workout.visible_for == "members_of_my_club",
                and_(
                    Workout.visible_for == "only_myself",
                    (Workout.created_by == id)
                    & (Workout.create_user_type == user_type),
                ).self_group(),
            ).self_group()
        )
    if params.goals:
        query = query.filter(Workout.goals == params.goals)
    if params.level:
        query = query.filter(Workout.level == params.level)
    if params.search:
        query = query.filter(Workout.workout_name.ilike(f"%{params.search}%"))
    if params.created_by_user:
        query = query.filter(
            Workout.create_user_type == user_type, Workout.created_by == id
        )
    return query

async def get_all_workout_table_view(
    db: Session,
    user: dict,
    params: WorkoutFilter,
    pagination_options: PaginationOptions,
):
    id, user_type, org_id = user["id"], user["user_type"], user["org_id"]
    exclude_by_default = {"days"}
    query = db.query(Workout).filter(
        Workout.is_deleted == False, Workout.org_id == org_id
    )
    query = workout_apply_filter(query,params,exclude_by_default, user)
    if params.equipment_id:
        query = (
            query.join(WorkoutDay, WorkoutDay.workout_id == Workout.id)
            .join(
                WorkoutDayExercise, WorkoutDayExercise.workout_day_id == WorkoutDay.id
            )
            .join(Exercise, Exercise.id == WorkoutDayExercise.exercise_id)
            .join(ExerciseEquipment, ExerciseEquipment.exercise_id == Exercise.id)
            .filter(ExerciseEquipment.equipment_id == params.equipment_id)
        )
    if pagination_options.offset:
        query = query.offset(pagination_options.offset)
    if pagination_options.limit:
        query = query.limit(pagination_options.limit)
    if params.sort_column:
        if params.sort_column not in _extract_columns(query):
            raise HTTPException(
                status_code=400, detail=f"Sort order must in {_extract_columns(query)}"
            )
        sort_order = (
            desc(params.sort_column)
            if params.sort_dir == "desc"
            else asc(params.sort_column)
        )
        query = query.order_by(sort_order)
    if params.include_days:
        query = query.options(joinedload(Workout.days))
        exclude_by_default = {"days": {"__all__": {"exercises"}}}
    if params.include_days_and_exercises:
        query = query.options(joinedload(Workout.days))
        exclude_by_default = {}

    items = query.all()
    return {
        "total": (
            db.query(func.count("*"))
            .filter(Workout.is_deleted == False, Workout.org_id == org_id)
            .scalar()
        ),
        "totalFiltered": _workout_get_count_before_pagination(db, user, params),
        "data": [
            WorkoutRead.model_validate(item).model_dump(exclude=exclude_by_default)
            for item in items
        ],
    }


def _group_by(arr: List[dict], key: str):
    groups = {}
    for a in arr:
        if a[key] not in groups:
            groups[a[key]] = []
        groups[a[key]].append(a)
    return [{"group": key, "data": group} for key, group in groups.items()]

async def get_all_workout_mobile_view(
    db: Session,
    user: dict,
    params: WorkoutMobileFilter,
):
    id, user_type, org_id = user["id"], user["user_type"], user["org_id"]
    exclude_by_default = {"days"}

    if params.sort_column and params.sort_column not in list(WorkoutRead.model_fields.keys()):
            raise HTTPException(
                status_code=400, detail=f"Sort order must in {list(WorkoutRead.model_fields.keys())}"
            )
    sort_order = (
        desc(params.sort_column if params.sort_column else Workout.id)
        if params.sort_dir == "desc"
        else asc(params.sort_column if params.sort_column else Workout.id)
    )
    GROUP_COLUMN = "goals"
    query = db.query(
        Workout,
        func.row_number()
        .over(partition_by=getattr(Workout, GROUP_COLUMN), order_by=sort_order)
        .label("row_num"),
    ).filter(Workout.is_deleted == False, Workout.org_id == org_id)
    query = workout_apply_filter(query,params,exclude_by_default, user)
    query = query.subquery()
    query_final = db.query(query).filter(query.c.row_num <= 3)
    items = [
        WorkoutRead.model_validate(item).model_dump(exclude=exclude_by_default)
        for item in query_final.all()
    ]
    return _group_by(items, GROUP_COLUMN)


async def get_workout_day_(db: Session, workout_day_id: int):
    return (
        db.query(WorkoutDay)
        .filter(WorkoutDay.id == workout_day_id, WorkoutDay.is_deleted == False)
        .first()
    )


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


async def get_workout_day_(
    db: Session, workout_day_id: int, include_exercises: bool = False
):
    return (
        db.query(WorkoutDay)
        .filter(WorkoutDay.id == workout_day_id, WorkoutDay.is_deleted == False)
        .first()
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
    if params.sort_column:
        if params.sort_column not in _extract_columns(query):
            raise HTTPException(
                status_code=400, detail=f"Sort order must in {_extract_columns(query)}"
            )
        sort_order = (
            desc(params.sort_column)
            if params.sort_dir == "desc"
            else asc(params.sort_column)
        )
        query = query.order_by(sort_order)
    return [
        WorkoutDayRead.model_validate(item).model_dump(exclude=exclude_by_default)
        for item in query.all()
    ]


async def save_workout_day(db: Session, workout: WorkoutDayCreate, user: dict):
    data = workout.model_dump()
    data["created_by"] = user["id"]
    data["create_user_type"] = user["user_type"]
    db_workout_day = WorkoutDay(**data)
    db.add(db_workout_day)
    db.commit()
    db.refresh(db_workout_day)
    return db_workout_day


async def save_workout_day_exercise(
    db: Session, workout_day_exercise: WorkoutDayExerciseCreate, user: dict
):
    data = workout_day_exercise.model_dump()
    data["created_by"] = user["id"]
    data["create_user_type"] = user["user_type"]
    db_workout_day_exercise = WorkoutDayExercise(**data)
    db.add(db_workout_day_exercise)
    db.commit()
    db.refresh(db_workout_day_exercise)
    return db_workout_day_exercise


async def get_all_workout_day_exercise(
    db: Session, params: WorkoutDayExerciseFilter, pagination_options: PaginationOptions
) -> List[WorkoutDayExerciseRead]:
    query = (
        db.query(
            *WorkoutDayExercise.__table__.columns,
            Exercise.exercise_name,
            Exercise.video_url_male,
            Exercise.gif_url,
        )
        .filter(WorkoutDayExercise.is_deleted == False)
        .outerjoin(Exercise, Exercise.id == WorkoutDayExercise.exercise_id)
    )
    if params.workout_day_id:
        query = query.filter(WorkoutDayExercise.workout_day_id == params.workout_day_id)
    if pagination_options.offset:
        query = query.offset(pagination_options.offset)
    if pagination_options.limit:
        query = query.limit(pagination_options.limit)
    return [WorkoutDayExerciseRead.model_validate(item) for item in query.all()]


async def get_workout_day_exercise(
    db: Session, user: dict, workout_day_exercise_id: int
) -> WorkoutDayExerciseRead:
    return (
        db.query(WorkoutDayExercise)
        .join(WorkoutDay, WorkoutDay.id == WorkoutDayExercise.workout_day_id)
        .join(Workout, Workout.id == WorkoutDay.workout_id)
        .filter(
            WorkoutDayExercise.id == workout_day_exercise_id,
            WorkoutDayExercise.is_deleted == False,
            Workout.org_id == user["org_id"],
        )
        .first()
    )
