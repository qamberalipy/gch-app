from typing import Annotated, Sequence
from pydantic import EmailStr
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Request

from .service import get_all_workout, get_all_workout_day, get_workout, get_workout_day, get_workout_day_exercise, save_workout, save_workout_day, save_workout_day_exercise, update_workout, update_workout_day, update_workout_day_exercise

from .models import Workout, WorkoutDay, WorkoutGoal, WorkoutLevel
from ..dependencies import get_db, get_user
from .schema import WorkoutCreate, WorkoutDayCreate, WorkoutDayExerciseCreate, WorkoutDayExerciseUpdate, WorkoutDayFilter, WorkoutDayRead, WorkoutDayUpdate, WorkoutFilter, WorkoutUpdate
from ..Client import schema as _client_schema


router = APIRouter(tags=["Workout router"])

async def verify_update_workout_day_exercise(day_exercise_id: Annotated[int,Path(description="Id of the workout day exercise")], 
                                    db: Annotated[Session, Depends(get_db)]):
     db_workout_day_exercise = await get_workout_day_exercise(db,day_exercise_id)
     if not db_workout_day_exercise:
             raise HTTPException(status_code=404, detail="Workout Day Exercise not found")
     return db_workout_day_exercise

async def verify_create_workout_day_exercise(workout_day_exercise: WorkoutDayExerciseCreate, db: Annotated[Session, Depends(get_db)]):
    workout_day = await get_workout_day(db,workout_day_exercise.workout_day_id)
    if not workout_day:
            raise HTTPException(status_code=404, detail="Workout Day not found")

async def verify_create_workout_day(workout_day: WorkoutDayCreate, db: Annotated[Session, Depends(get_db)]):
    workout = await get_workout(db,workout_day.workout_id)
    if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")

    params = WorkoutDayFilter(workout_id=workout_day.workout_id, week=workout_day.week,
                            day=workout_day.day)
    existing_workout_day = await get_all_workout_day(db, params=params)

    if existing_workout_day:
        raise HTTPException(status_code=400, detail=f"Workout day with week {workout_day.week} and day {workout_day.day} already exists")

    if workout_day.week > workout.weeks:
        raise HTTPException(status_code=400, detail="Week exceeds the number of weeks in the workout")

async def verify_update_workout_day(workout_day: WorkoutDayUpdate, 
                                    day_id: Annotated[int,Path(description="Id of the workout day")], 
                                    db: Annotated[Session, Depends(get_db)]):
     db_workout_day = await get_workout_day(db,day_id)
     if not db_workout_day:
             raise HTTPException(status_code=404, detail="Workout Day not found")

     if workout_day.week or workout_day.day:
         week= workout_day.week or db_workout_day.week
         day= workout_day.day or db_workout_day.day
         params = WorkoutDayFilter(workout_id= db_workout_day.workout_id, week=week, day=day)

         existing_workout_day = await get_all_workout_day(db, params=params)

         if existing_workout_day and existing_workout_day[0].id != day_id:
                 raise HTTPException(status_code=400, detail=f"Workout day with week {week} and day {day} already exists")

     workout = await get_workout(db,db_workout_day.workout_id)
     if workout_day.week and workout_day.week > workout.weeks:
         raise HTTPException(status_code=400, detail="Week exceeds the number of weeks in the workout")
     return db_workout_day

def get_filters(goals: Annotated[WorkoutGoal | None, Query(title="Workout Goal")] = None,
                level: Annotated[WorkoutLevel | None, Query(title="Workout Level")] = None,
                _search: Annotated[str | None, Query(title="Search", description="Search workout by name")] = None
                ):
    return WorkoutFilter(goals=goals, level=level, search=_search)

@router.post("/day/exercise", dependencies=[Depends(verify_create_workout_day_exercise)])
async def save_exercise(
        workout_day_exercise: WorkoutDayExerciseCreate,
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[_client_schema.ClientRead, Depends(get_user)],
        ):
    try:
        return await save_workout_day_exercise(db, workout_day_exercise, user_id=user.id)
    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input") 
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 

@router.put("/day/exercise/{workout_day_exercise_id}")
async def update_exercise(workout_day_exercise: WorkoutDayExerciseUpdate,
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[_client_schema.ClientRead, Depends(get_user)],
        workout_day_exercise_model: Annotated[WorkoutDay, Depends(verify_update_workout_day)]):
    try:
        return await update_workout_day_exercise(db, workout_day_exercise_model, workout_day_exercise, user_id=user.id)
    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input") 
    except HTTPException as e:
        db.rollback()
        raise e 

@router.post("/day", dependencies=[Depends(verify_create_workout_day)])
async def save_day(
        workout_day: WorkoutDayCreate,
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[_client_schema.ClientRead, Depends(get_user)],
        ):
    try:
        return await save_workout_day(db, workout_day, user_id=user.id)
    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input") 
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unknown exception occured") 

@router.put("/day/{day_id}")
async def update_day(day_id: int,
        workout_day: WorkoutDayUpdate,
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[_client_schema.ClientRead, Depends(get_user)],
        workout_day_model: Annotated[WorkoutDay, Depends(verify_update_workout_day)]):
    try:
        return await update_workout_day(db, workout_day_model, workout_day, user_id=user.id)
    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input") 
    except HTTPException as e:
        db.rollback()
        raise e 

@router.post("/")
async def save(
        workout: WorkoutCreate,
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[_client_schema.ClientRead, Depends(get_user)]):
    try:
        return await save_workout(db, workout, user_id=user.id)
    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input") 
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unknown exception occured") 

@router.put("/{workout_id}")
async def update(workout_id: int,
        workout: WorkoutUpdate,
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[_client_schema.ClientRead, Depends(get_user)]):
    try:
        return await update_workout(db, workout_id, workout, user_id=user.id)
    except DataError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Data error occurred, check your input") 
    except HTTPException as e:
        db.rollback()
        raise e 

@router.get("/day")
async def get_all_day(db: Annotated[Session, Depends(get_db)]):
    return await get_all_workout_day(db, WorkoutDayFilter())

@router.get("/day/{day_id}")
async def get_one_day(day_id: Annotated[int,Path(description="Id of the workout day")],
                  db: Annotated[Session, Depends(get_db)]):
    workout = await get_workout_day(db, day_id)
    if not workout:
            raise HTTPException(status_code=404, detail="Workout day not found")
    return workout

@router.get("/")
async def get_all(db: Annotated[Session, Depends(get_db)],
                  filters: Annotated[WorkoutFilter, Depends(get_filters)]
                  ):
    return await get_all_workout(db, filters)

@router.get("/{workout_id}")
async def get_one(workout_id: Annotated[int,Path(description="Id of the workout")], 
                  db: Annotated[Session, Depends(get_db)]):
    workout = await get_workout(db, workout_id)
    if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")
    return workout

