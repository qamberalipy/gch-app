from datetime import datetime
from typing import List
from typing_extensions import Optional
from pydantic import BaseModel, Field

from app.Workout.models import ExerciseIntensity, ExerciseType, WorkoutGoal, WorkoutLevel


class WorkoutBase(BaseModel):
    workout_name: str
    description: Optional[str] = None
    goals: WorkoutGoal
    level: WorkoutLevel
    notes: Optional[str] = None
    weeks: int = Field(ge=1)

class WorkoutCreate(WorkoutBase):
    pass

class WorkoutRead(WorkoutBase):
    pass


class WorkoutUpdate(BaseModel):
    workout_name: Optional[str] = None
    description: Optional[str] = None
    goals: Optional[WorkoutGoal] = None
    level: Optional[WorkoutLevel] = None
    notes: Optional[str] = None
    weeks: Optional[int] = None

class WorkoutFilter(BaseModel):
    workout_name: Optional[str] = None
    goals: Optional[WorkoutGoal] = None
    level: Optional[WorkoutLevel] = None
    search: Optional[str] = None


class WorkoutDayBase(BaseModel):
    workout_id: int
    day_name: str
    week: int = Field(ge=1)
    day: int = Field(ge=1, le=7)

class WorkoutDayCreate(WorkoutDayBase):
    pass


class WorkoutDayRead(WorkoutDayBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    is_deleted: bool

class WorkoutDayOptionalBase(BaseModel):
    day_name: Optional[str] = None
    week: Optional[int] = Field(default=None, ge=1)
    day: Optional[int] = Field(default=None, ge=1, le=7)

class WorkoutDayUpdate(WorkoutDayOptionalBase):
    pass

class WorkoutDayFilter(WorkoutDayOptionalBase):
    workout_id: Optional[int] = None

class WorkoutDayExerciseBase(BaseModel):
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

class WorkoutDayExerciseCreate(WorkoutDayExerciseBase):
    pass

class WorkoutDayExerciseRead(WorkoutDayExerciseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    is_deleted: bool

class WorkoutDayExerciseUpdate(BaseModel):
    exercise_id: Optional[int] = None
    exercise_type: Optional[ExerciseType] = None
    sets: Optional[int] = Field(default=None, ge=0)
    seconds_per_set: Optional[List[int]] = None
    repetitions_per_set: Optional[List[int]] = None
    rest_between_set: Optional[List[int]] = None
    intensity_type: ExerciseIntensity
    percentage_of_1rm: Optional[float] = None
    notes: Optional[str] = None
