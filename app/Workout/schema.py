from datetime import datetime
from typing import Annotated, List
from typing_extensions import Optional
from pydantic import AfterValidator, BaseModel, Field, validator

from .models import ExerciseIntensity, ExerciseType, WorkoutGoal, WorkoutLevel


class MyBaseModel(BaseModel):
    class Config:
        extra = 'forbid'
        from_attributes = True

class WorkoutDayBase(MyBaseModel):
    workout_id: int
    day_name: str
    week: int = Field(ge=1)
    day: int = Field(ge=1, le=7)

class WorkoutDayExerciseBase(MyBaseModel):
    workout_day_id: int
    exercise_id: int
    exercise_type: ExerciseType
    sets: int = Field(ge=0)
    seconds_per_set: Optional[List[int]] = None
    repetitions_per_set: Optional[List[int]] = None
    rest_between_set: Optional[List[int]] = None
    intensity_type: ExerciseIntensity
    percentage_of_1rm: Optional[float] = None
    notes: Optional[str] = None

class WorkoutDayExerciseRead(WorkoutDayExerciseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    is_deleted: bool

class WorkoutDayRead(WorkoutDayBase):
    id: int
    exercises: Optional[List[WorkoutDayExerciseRead]] = None
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    is_deleted: bool

class WorkoutBase(MyBaseModel):
    workout_name: str
    description: Optional[str] = None
    goals: WorkoutGoal
    level: WorkoutLevel
    notes: Optional[str] = None
    weeks: int = Field(ge=1)

class WorkoutCreate(WorkoutBase):
    pass

def check_empty(v):
    return None if len(v) == 0 else v

class WorkoutRead(WorkoutBase):
    id: int
    days: Annotated[None | List[WorkoutDayRead], AfterValidator(check_empty)]


class WorkoutUpdate(MyBaseModel):
    workout_name: Optional[str] = None
    description: Optional[str] = None
    goals: Optional[WorkoutGoal] = None
    level: Optional[WorkoutLevel] = None
    notes: Optional[str] = None
    weeks: Optional[int] = None

class WorkoutFilter(MyBaseModel):
    workout_name: Optional[str] = None
    goals: Optional[WorkoutGoal] = None
    level: Optional[WorkoutLevel] = None
    search: Optional[str] = None
    include_days: Optional[bool] = False
    include_days_and_exercises: Optional[bool] = False

class WorkoutDayCreate(WorkoutDayBase):
    pass

class WorkoutDayOptionalBase(MyBaseModel):
    day_name: Optional[str] = None
    week: Optional[int] = Field(default=None, ge=1)
    day: Optional[int] = Field(default=None, ge=1, le=7)

class WorkoutDayUpdate(WorkoutDayOptionalBase):
    pass

class WorkoutDayFilter(WorkoutDayOptionalBase):
    workout_id: Optional[int] = None
    include_exercises: Optional[bool] = None


class WorkoutDayExerciseCreate(WorkoutDayExerciseBase):
    pass

class WorkoutDayExerciseOptionalBase(MyBaseModel):
    exercise_id: Optional[int] = None
    exercise_type: Optional[ExerciseType] = None
    sets: Optional[int] = Field(default=None, ge=0)
    seconds_per_set: Optional[List[int]] = None
    repetitions_per_set: Optional[List[int]] = None
    rest_between_set: Optional[List[int]] = None
    intensity_type: Optional[ExerciseIntensity] = None
    percentage_of_1rm: Optional[float] = None
    notes: Optional[str] = None

class WorkoutDayExerciseUpdate(WorkoutDayExerciseOptionalBase):
    pass

class WorkoutDayExerciseFilter(WorkoutDayExerciseOptionalBase):
    workout_day_id: Optional[int] = None

