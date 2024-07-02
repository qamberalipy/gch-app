
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative
from enum import Enum as PyEnum
from datetime import datetime

class ExerciseType(PyEnum):
    time_based = 'Time Based'
    repetition_based = 'Repetition Based'


class VisibleFor(PyEnum):
    only_myself = 'Only Myself'
    staff_of_my_club = 'Staff of My Club'
    members_of_my_club = 'Members of My Club'
    everyone_in_my_club = 'Everyone in My Club'


class Exercise(_database.Base):
    __tablename__ = 'exercise'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    exercise_name = _sql.Column(_sql.String, nullable=False)
    visible_for = _sql.Column(_sql.Enum(VisibleFor), nullable=False)
    exercise_category_id = _sql.Column(_sql.Integer, nullable=False)  # Foreign key reference to app.exercisecategory
    equipment_id = _sql.Column(_sql.Integer, nullable=True)  # Foreign key reference to app.equipments
    primary_muscle_id = _sql.Column(_sql.Integer, nullable=True)  # Foreign key reference to app.primarymuscle
    secondary_muscle_id = _sql.Column(_sql.Integer, nullable=True)  # Foreign key reference to app.secondarymuscle
    primary_joint_id = _sql.Column(_sql.Integer, nullable=True)  # Foreign key reference to app.primaryjoint
    exercise_type = _sql.Column(_sql.String, nullable=False)  # Consider using Enum in DB for better constraint
    sets = _sql.Column(_sql.Integer, nullable=True)  # Conditional based on exercise type
    seconds_per_set = _sql.Column(_sql.ARRAY(_sql.Integer), nullable=True)  # Conditional based on exercise type
    repetitions_per_set = _sql.Column(_sql.ARRAY(_sql.Integer), nullable=True)  # Conditional based on exercise type
    rest_after_set = _sql.Column(_sql.ARRAY(_sql.Integer), nullable=True)  # Conditional based on exercise type
    met_id = _sql.Column(_sql.Integer, nullable=True)  # Foreign key reference to app.MET, optional
    gif_url = _sql.Column(_sql.String, nullable=True)
    video_url = _sql.Column(_sql.String, nullable=True)
    thumbnail = _sql.Column(_sql.String, nullable=True)  # File path or URL for the image
    created_at = _sql.Column(_sql.DateTime, default=datetime.utcnow)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExerciseCategory(_database.Base):
    __tablename__ = 'exercisecategory'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    category_name = _sql.Column(_sql.String, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=datetime.utcnow)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Equipment(_database.Base):
    __tablename__ = 'equipments'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    equipment_name = _sql.Column(_sql.String, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=datetime.utcnow)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PrimaryMuscle(_database.Base):
    __tablename__ = 'primarymuscle'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    muscle_name = _sql.Column(_sql.String, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=datetime.utcnow)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecondaryMuscle(_database.Base):
    __tablename__ = 'secondarymuscle'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    muscle_name = _sql.Column(_sql.String, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=datetime.utcnow)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PrimaryJoint(_database.Base):
    __tablename__ = 'primaryjoint'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    joint_name = _sql.Column(_sql.String, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=datetime.utcnow)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MET(_database.Base):
    __tablename__ = 'met'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    met_value = _sql.Column(_sql.Float, nullable=False)
    met_description = _sql.Column(_sql.String, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=datetime.utcnow)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


