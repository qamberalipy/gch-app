from typing import Annotated, Any, Literal, Sequence
from pydantic import EmailStr
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Request

from .service import (
    delete_workout,
    delete_workout_day,
    delete_workout_day_exercise,
    get_all_workout_day,
    get_all_workout_day_exercise,
    get_all_workout_mobile_view,
    get_all_workout_table_view,
    get_workout,
    get_workout_day,
    get_workout_day_,
    get_workout_day_exercise,
    save_workout,
    save_workout_day,
    save_workout_day_exercise,
    update_workout,
    update_workout_day,
    update_workout_day_exercise,
)

from .models import Workout, WorkoutDay, WorkoutDayExercise, WorkoutGoal, WorkoutLevel
from ..Shared.dependencies import (
    get_db,
    get_module_permission,
    get_pagination_options,
    get_user,
)
from ..Shared.schema import PaginationOptions
from .schema import (
    WorkoutCreate,
    WorkoutDayCreate,
    WorkoutDayExerciseCreate,
    WorkoutDayExerciseFilter,
    WorkoutDayExerciseUpdate,
    WorkoutDayFilter,
    WorkoutDayRead,
    WorkoutDayUpdate,
    WorkoutFilter,
    WorkoutMobileFilter,
    WorkoutRead,
    WorkoutUpdate,
)
from ..Client import schema as _client_schema
from ..Exercise import service as _exercise_service

API_STR = "/workout_plans"
router = APIRouter(prefix=API_STR, tags=["Workout router"])
get_read_permission = get_module_permission("Workout Plans", "read")
get_write_permission = get_module_permission("Workout Plans", "write")
get_delete_permission = get_module_permission("Workout Plans", "delete")


async def verify_update_workout_day_exercise(
    workout_day_exercise: WorkoutDayExerciseUpdate,
    workout_day_exercise_id: Annotated[
        int, Path(description="Id of the workout day exercise")
    ],
    db: Annotated[Session, Depends(get_db)],
):
    db_workout_day_exercise = await get_workout_day_exercise(
        db, workout_day_exercise_id
    )
    if not db_workout_day_exercise:
        raise HTTPException(status_code=404, detail="Workout Day Exercise not found")
    if workout_day_exercise.exercise_id:
        exercise = await _exercise_service.get_exercise_by_id(
            workout_day_exercise.exercise_id, db
        )
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
    return db_workout_day_exercise


async def verify_create_workout_day_exercise(
    workout_day_exercise: WorkoutDayExerciseCreate,
    db: Annotated[Session, Depends(get_db)],
):
    workout_day = await get_workout_day_(db, workout_day_exercise.workout_day_id)
    if not workout_day:
        raise HTTPException(status_code=404, detail="Workout Day not found")
    exercise = await _exercise_service.get_exercise_by_id(
        workout_day_exercise.exercise_id, db
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")


async def verify_create_workout_day(
    workout_day: WorkoutDayCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[dict, Depends(get_user)],
):
    workout = await get_workout(db, user["org_id"], workout_day.workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    params = WorkoutDayFilter(
        workout_id=workout_day.workout_id, week=workout_day.week, day=workout_day.day
    )
    existing_workout_day = await get_all_workout_day(db, params, PaginationOptions())

    if existing_workout_day:
        raise HTTPException(
            status_code=400,
            detail=f"Workout day with week {workout_day.week} and day {workout_day.day} already exists",
        )

    if workout_day.week > workout.weeks:
        raise HTTPException(
            status_code=400, detail="Week exceeds the number of weeks in the workout"
        )


async def verify_update_workout_day(
    workout_day: WorkoutDayUpdate,
    day_id: Annotated[int, Path(description="Id of the workout day")],
    db: Annotated[Session, Depends(get_db)],
):
    db_workout_day = await get_workout_day(db, day_id)
    if not db_workout_day:
        raise HTTPException(status_code=404, detail="Workout Day not found")

    if workout_day.week or workout_day.day:
        week = workout_day.week or db_workout_day.week
        day = workout_day.day or db_workout_day.day
        params = WorkoutDayFilter(
            workout_id=db_workout_day.workout_id, week=week, day=day
        )

        existing_workout_day = await get_all_workout_day(db, params=params)

        if existing_workout_day and existing_workout_day[0].id != day_id:
            raise HTTPException(
                status_code=400,
                detail=f"Workout day with week {week} and day {day} already exists",
            )

    workout = await get_workout(db, db_workout_day.workout_id)
    if workout_day.week and workout_day.week > workout.weeks:
        raise HTTPException(
            status_code=400, detail="Week exceeds the number of weeks in the workout"
        )
    return db_workout_day


async def verify_delete_workout_day(
    day_id: Annotated[int, Path(description="Id of the workout day")],
    db: Annotated[Session, Depends(get_db)],
):
    db_workout_day = await get_workout_day(db, day_id)
    if not db_workout_day:
        raise HTTPException(status_code=404, detail="Workout Day not found")

    return db_workout_day


async def verify_delete_workout_day_exercise(
    workout_day_exercise_id: Annotated[
        int, Path(description="Id of the workout day exercise")
    ],
    db: Annotated[Session, Depends(get_db)],
):
    db_workout_day_exercise = await get_workout_day_exercise(
        db, workout_day_exercise_id
    )
    if not db_workout_day_exercise:
        raise HTTPException(status_code=404, detail="Workout Day Exercise not found")
    return db_workout_day_exercise


async def verify_workout(
    db: Annotated[Session, Depends(get_db)],
    workout_id: Annotated[int, Path(description="Id of the workout")],
):
    workout_model = get_workout(db, workout_id)
    if not workout_model:
        raise HTTPException(status_code=404, detail="Workout doesn't exist")
    return workout_model


#workout_columns = list(WorkoutRead.model_fields.keys())
def get_filters(
    goals: Annotated[WorkoutGoal | None, Query(title="Workout Goal")] = None,
    level: Annotated[WorkoutLevel | None, Query(title="Workout Level")] = None,
    equipment_id: Annotated[int | None, Query(title="Filter workouts by equipment")] = None,
    _search: Annotated[
        str | None, Query(title="Search", description="Search workout by name")
    ] = None,
    _include_days: Annotated[
        bool,
        Query(title="Days", description="Whether to includes days of that workout"),
    ] = False,
    _include_days_and_exercises: Annotated[
        bool, Query(description="To include that workout's days and exercises")
    ] = False,
    _sort_column: Annotated[
        str | None, Query(description="The column to sort")
    ] = None,
    _sort_dir: Annotated[
        Literal["asc", "desc"],
        Query(
            description="The direction to sort the column in like [asc]ending and [desc]ending"
        ),
    ] = "asc",
    _results_per_goal: Annotated[
        int,
        Query(
            description="The direction to sort the column in like [asc]ending and [desc]ending"
        ),
    ] = 3,
):
    return WorkoutFilter(
        goals=goals,
        level=level,
        search=_search,
        include_days=_include_days,
        include_days_and_exercises=_include_days_and_exercises,
        sort_column=_sort_column,
        sort_dir=_sort_dir,
        results_per_goal=_results_per_goal,
        equipment_id=equipment_id,
    )


# @router.get("/day/exercise", dependencies=[Depends(get_read_permission)])
# async def get_all_day_exercise(
#     db: Annotated[Session, Depends(get_db)],
#     pagination_options: Annotated[PaginationOptions, Depends(get_pagination_options)],
# ):
#     return await get_all_workout_day_exercise(
#         db, WorkoutDayExerciseFilter(), pagination_options
#     )


# @router.get(
#     "/day/exercise/{workout_day_exercise_id}",
#     dependencies=[Depends(get_read_permission)],
# )
# async def get_one_exercise(
#     workout_day_exercise_id: Annotated[int, Path(description="Id of the workout day")],
#     db: Annotated[Session, Depends(get_db)],
# ):
#     workout_day_exercise = await get_workout_day_exercise(db, workout_day_exercise_id)
#     if not workout_day_exercise:
#         raise HTTPException(status_code=404, detail="Workout day not found")
#     return workout_day_exercise


@router.post(
    "/day/exercise",
    dependencies=[
        Depends(verify_create_workout_day_exercise),
        Depends(get_write_permission),
    ],
)
async def save_exercise(
    workout_day_exercise: WorkoutDayExerciseCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[dict, Depends(get_user)],
):
    try:
        return await save_workout_day_exercise(db, workout_day_exercise, user)
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/day/exercise/{workout_day_exercise_id}",
    dependencies=[Depends(get_write_permission)],
)
async def update_exercise(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[_client_schema.ClientRead, Depends(get_user)],
    workout_day_exercise: WorkoutDayExerciseUpdate,
    workout_day_exercise_model: Annotated[
        WorkoutDay, Depends(verify_update_workout_day_exercise)
    ],
):
    try:
        return await update_workout_day_exercise(
            db, workout_day_exercise_model, workout_day_exercise, user_id=user.id
        )
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )
    except HTTPException as e:
        db.rollback()
        raise e


@router.delete(
    "/day/exercise/{workout_day_exercise_id}",
    dependencies=[Depends(get_delete_permission)],
)
async def delete_exercise(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[_client_schema.ClientRead, Depends(get_user)],
    workout_day_exercise_model: Annotated[
        WorkoutDayExercise, Depends(verify_delete_workout_day_exercise)
    ],
):
    try:
        return await delete_workout_day_exercise(
            db, workout_day_exercise_model, user_id=user.id
        )
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )
    except HTTPException as e:
        db.rollback()
        raise e


@router.get(
    "/day/{workout_day_id}/exercise", dependencies=[Depends(get_read_permission)]
)
async def get_one_day_exercise(
    workout_day_id: Annotated[int, Path(description="Id of the workout")],
    db: Annotated[Session, Depends(get_db)],
):
    return await get_all_workout_day_exercise(
        db, WorkoutDayExerciseFilter(workout_day_id=workout_day_id), PaginationOptions()
    )


@router.get("/day", dependencies=[Depends(get_read_permission)])
async def get_all_day(
    db: Annotated[Session, Depends(get_db)],
    pagination_options: Annotated[PaginationOptions, Depends(get_pagination_options)],
    _include_exercises: Annotated[
        bool,
        Query(
            description="Whether the days should include the exercises associated with that day"
        ),
    ] = False,
):
    return await get_all_workout_day(
        db, WorkoutDayFilter(include_exercises=_include_exercises), pagination_options
    )


# @router.get("/day/{day_id}", dependencies=[Depends(get_read_permission)])
# async def get_one_day(
#     day_id: Annotated[int, Path(description="Id of the workout day")],
#     db: Annotated[Session, Depends(get_db)],
#     _include_exercises: Annotated[
#         bool,
#         Query(
#             description="Whether the days should include the exercises associated with that day"
#         ),
#     ] = False,
# ):
#     workout = await get_workout_day(db, day_id, _include_exercises)
#     if not workout:
#         raise HTTPException(status_code=404, detail="Workout day not found")
#     return workout


workout_day_columns = list(WorkoutDayRead.model_fields.keys())


@router.get("/{workout_id}/day", dependencies=[Depends(get_read_permission)])
async def get_day_by_workout_id(
    workout_id: Annotated[int, Path(description="Id of the workout")],
    db: Annotated[Session, Depends(get_db)],
    pagination_options: Annotated[PaginationOptions, Depends(get_pagination_options)],
    _include_exercises: Annotated[
        bool,
        Query(
            description="Whether the days should include the exercises associated with that day"
        ),
    ] = False,
    _sort_column: Annotated[
        Literal[*tuple(workout_day_columns)] | None,
        Query(description="The column to sort"),
    ] = None,
    _sort_dir: Annotated[
        Literal["asc", "desc"],
        Query(
            description="The direction to sort the column in like [asc]ending and [desc]ending"
        ),
    ] = "asc",
):
    return await get_all_workout_day(
        db,
        WorkoutDayFilter(
            workout_id=workout_id,
            include_exercises=_include_exercises,
            sort_column=_sort_column,
            sort_dir=_sort_dir,
        ),
        pagination_options,
    )


@router.post(
    "/day",
    dependencies=[Depends(verify_create_workout_day), Depends(get_write_permission)],
)
async def save_day(
    workout_day: WorkoutDayCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[dict, Depends(get_user)],
):
    try:
        return await save_workout_day(db, workout_day, user)
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unknown exception occured")


@router.put("/day/{day_id}", dependencies=[Depends(get_write_permission)])
async def update_day(
    day_id: int,
    workout_day: WorkoutDayUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[_client_schema.ClientRead, Depends(get_user)],
    workout_day_model: Annotated[WorkoutDay, Depends(verify_update_workout_day)],
):
    try:
        return await update_workout_day(
            db, workout_day_model, workout_day, user_id=user.id
        )
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )
    except HTTPException as e:
        db.rollback()
        raise e


@router.delete("/day/{day_id}", dependencies=[Depends(get_delete_permission)])
async def delete_day(
    day_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[_client_schema.ClientRead, Depends(get_user)],
    workout_day_model: Annotated[WorkoutDay, Depends(verify_delete_workout_day)],
):
    try:
        return await delete_workout_day(db, day_id, workout_day_model, user_id=user.id)
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )
    except HTTPException as e:
        db.rollback()
        raise e


@router.get("")
async def get_all(
    db: Annotated[Session, Depends(get_db)],
    filters: Annotated[WorkoutFilter, Depends(get_filters)],
    pagination_options: Annotated[PaginationOptions, Depends(get_pagination_options)],
    user: Annotated[dict, Depends(get_user)],
):
        return await get_all_workout_table_view(db, user, filters, pagination_options)

#@router.get("mobile/workout_plans")
#async def get_all_mobile(
#    db: Annotated[Session, Depends(get_db)],
#    filters: Annotated[WorkoutMobileFilter, Depends()],
#    user: Annotated[dict, Depends(get_user)],
#):
#        return await get_all_workout_mobile_view(db, user, filters)

@router.get("/{workout_id}", dependencies=[Depends(get_read_permission)])
async def get_one(
    workout_id: Annotated[int, Path(description="Id of the workout")],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[dict, Depends(get_user)],
    _include_days: Annotated[
        bool, Query(description="To include that workout's days")
    ] = False,
    _include_days_and_exercises: Annotated[
        bool, Query(description="To include that workout's days and exercises")
    ] = False,
):
    workout = await get_workout(
        db, workout_id, user["org_id"], _include_days, _include_days_and_exercises
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.post("", dependencies=[Depends(get_write_permission)])
async def save(
    workout: WorkoutCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[dict, Depends(get_user)],
):
    try:
        return await save_workout(db, user, workout)
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unknown exception occured")


@router.put("/{workout_id}", dependencies=[Depends(get_write_permission)])
async def update(
    workout_model: Annotated[Workout, Depends(verify_workout)],
    workout: WorkoutUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[_client_schema.ClientRead, Depends(get_user)],
):
    try:
        return await update_workout(db, workout_model, workout, user_id=user.id)
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )
    except HTTPException as e:
        db.rollback()
        raise e


@router.delete("/{workout_id}", dependencies=[Depends(get_delete_permission)])
async def delete(
    workout_id: int,
    workout_model: Annotated[Workout, Depends(verify_workout)],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[_client_schema.ClientRead, Depends(get_user)],
):
    try:
        return await delete_workout(db, workout_id, workout_model, user_id=user.id)
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Data error occurred, check your input"
        )
    except HTTPException as e:
        db.rollback()
        raise e
