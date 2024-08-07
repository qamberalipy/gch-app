import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative
from enum import Enum as PyEnum
from datetime import datetime


class Intensity(str,PyEnum):
    irm='%IRM'
    max_intensity='Max Intensity'

class Difficulty(str,PyEnum):
    Novice='Novice'
    Beginner='Beginner'
    Intermediate='Intermediate'
    Advance='Advance'
    Expert='Expert'

class ExerciseType(str,PyEnum):
    time_based = 'Time Based'
    repetition_based = 'Repetition Based'

class VisibleFor(str,PyEnum):
    only_myself = 'Only Myself'
    staff_of_my_club = 'Staff of My Club'
    members_of_my_club = 'Members of My Club'
    everyone_in_my_club = 'Everyone in My Club'

class Exercise(_database.Base):
    __tablename__ = 'exercise'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    org_id=_sql.Column(_sql.Integer)
    exercise_name = _sql.Column(_sql.String, nullable=False)
    visible_for = _sql.Column(_sql.Enum(VisibleFor), nullable=False)
    category_id = _sql.Column(_sql.Integer, nullable=False) 
    exercise_intensity= _sql.Column(_sql.Enum(Intensity), nullable=False)  
    intensity_value=_sql.Column(_sql.Float, nullable=True)
    exercise_type = _sql.Column(_sql.String, nullable=False)  
    difficulty= _sql.Column(_sql.Enum(Difficulty), nullable=False)
    sets = _sql.Column(_sql.Integer, nullable=True) 
    seconds_per_set = _sql.Column(_sql.ARRAY(_sql.Integer), nullable=True) 
    repetitions_per_set = _sql.Column(_sql.ARRAY(_sql.Integer), nullable=True) 
    rest_between_set = _sql.Column(_sql.ARRAY(_sql.Integer), nullable=True)  
    distance= _sql.Column(_sql.Float, nullable=True)
    speed= _sql.Column(_sql.Float, nullable=True)
    met_id = _sql.Column(_sql.Integer, nullable=True)  
    gif_url = _sql.Column(_sql.String, nullable=True)
    video_url_male = _sql.Column(_sql.String, nullable=True)
    video_url_female = _sql.Column(_sql.String, nullable=True)
    thumbnail_male = _sql.Column(_sql.String, nullable=True)
    thumbnail_female = _sql.Column(_sql.String, nullable=True)
    image_url_female = _sql.Column(_sql.String, nullable=True)
    image_url_male = _sql.Column(_sql.String, nullable=True)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
class Equipment(_database.Base):
    __tablename__ = 'equipments'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    equipment_name = _sql.Column(_sql.String, nullable=False)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)   
    is_deleted = _sql.Column(_sql.Boolean, default=False)

class ExerciseEquipment(_database.Base):
    __tablename__ = 'exercise_equipment'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    exercise_id=_sql.Column(_sql.Integer, index=True)
    equipment_id=_sql.Column(_sql.Integer)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
class ExerciseCategory(_database.Base):
    __tablename__ = 'exercise_category'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    category_name = _sql.Column(_sql.String, nullable=False)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = _sql.Column(_sql.Boolean, default=False)
class Muscle(_database.Base):
    __tablename__ = 'muscle'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    muscle_name = _sql.Column(_sql.String, nullable=False)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = _sql.Column(_sql.Boolean, default=False)
    

class PrimaryJoint(_database.Base):
    __tablename__ = 'primary_joint'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    joint_name = _sql.Column(_sql.String, nullable=False)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = _sql.Column(_sql.Boolean, default=False)

class ExercisePrimaryMuscle(_database.Base):
    __tablename__ = 'exercise_primary_muscle'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    exercise_id=_sql.Column(_sql.Integer)
    muscle_id=_sql.Column(_sql.Integer)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = _sql.Column(_sql.Boolean, default=False)

class ExerciseSecondaryMuscle(_database.Base):
    __tablename__ = 'exercise_secondary_muscle'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    exercise_id=_sql.Column(_sql.Integer)
    muscle_id=_sql.Column(_sql.Integer)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = _sql.Column(_sql.Boolean, default=False)

class ExercisePrimaryJoint(_database.Base):
    __tablename__ = 'exercise_primary_joint'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    exercise_id=_sql.Column(_sql.Integer)
    primary_joint_id=_sql.Column(_sql.Integer)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = _sql.Column(_sql.Boolean, default=False)

class MET(_database.Base):
    __tablename__ = 'met'

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    met_value = _sql.Column(_sql.String, nullable=False)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = _sql.Column(_sql.Boolean, default=False)


