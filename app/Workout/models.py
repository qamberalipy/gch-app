from sqlalchemy import Boolean, Column, Float, Integer, String, Enum, DateTime, ARRAY
from sqlalchemy.orm import relationship
from ..core.db import session as _database
from datetime import datetime
from enum import Enum as PyEnum


class ExerciseType(PyEnum):
    time_based = "Time Based"
    repetition_based = "Repetition Based"


class ExerciseIntensity(PyEnum):
    max = "Max"
    percentage_of_1rm = "% of 1RM"


class WorkoutGoal(PyEnum):
    lose_weight = "Lose Weight"
    build_muscle = "Build Muscle"
    improved_well_being = "Improved well being"
    improve_performance = "Improve Performance"
    rehabilitation = "Rehabilitation"
    get_fit = "Get Fit"
    shape_and_tone = "Shape and Tone"


class WorkoutLevel(PyEnum):
    novice = "Novice"
    beginner = "Beginner"
    intermediate = "Intermediate"
    advanced = "Advanced"
    expert = "Expert"


class Workout(_database.Base):
    __tablename__ = "workout"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    org_id = Column(Integer)
    workout_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    goals = Column(Enum(WorkoutGoal), nullable=False)
    level = Column(Enum(WorkoutLevel), nullable=False)
    notes = Column(String, nullable=True)
    weeks = Column(Integer, nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False)

    days = relationship(
        "WorkoutDay",
        primaryjoin="Workout.id == foreign(WorkoutDay.workout_id)",
        lazy='noload',
        back_populates="workout",
    )


class WorkoutDay(_database.Base):
    __tablename__ = "workout_day"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workout_id = Column(Integer, nullable=False)
    day_name = Column(String, nullable=False)
    week = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False)

    workout = relationship(
        "Workout",
        primaryjoin="Workout.id == foreign(WorkoutDay.workout_id)",
        lazy='noload',
        back_populates="days",
    )
    exercises = relationship(
        "WorkoutDayExercise",
        primaryjoin="WorkoutDay.id == foreign(WorkoutDayExercise.id)",
        lazy='noload',
        back_populates="workout_day",
    )


class WorkoutDayExercise(_database.Base):
    __tablename__ = "workout_day_exercise"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workout_day_id = Column(Integer, nullable=False)
    exercise_id = Column(Integer, nullable=False)
    exercise_type = Column(Enum(ExerciseType), nullable=False)
    sets = Column(Integer, nullable=False)
    seconds_per_set = Column(ARRAY(Integer), nullable=True)
    repetitions_per_set = Column(ARRAY(Integer), nullable=True)
    rest_between_set = Column(ARRAY(Integer), nullable=True)
    intensity_type = Column(Enum(ExerciseIntensity), default=ExerciseIntensity.max)
    percentage_of_1rm = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    created_by = Column(Integer)
    updated_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False)

    workout_day = relationship(
        "WorkoutDay",
        primaryjoin="WorkoutDay.id == foreign(WorkoutDayExercise.id)",
        back_populates="exercises",
    )
