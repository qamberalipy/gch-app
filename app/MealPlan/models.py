import datetime as _dt
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative
from enum import Enum as PyEnum

class MealTimeEnum(PyEnum):
    Breakfast = "Breakfast"
    Morning_Snack = "Morning Snack"
    Lunch = "Lunch"
    Afternoon_Snack = "Afternoon Snack"
    Dinner = "Dinner"
    Evening_Snack = "Evening Snack"
    
class VisibleForEnum(PyEnum):
    only_myself = "Only myself"
    staff = "Staff of my gym"
    members =  "Members of my gym"
    everyone = "Everyone in my gym"
    
class MealPlan(_database.Base):
    __tablename__ = "meal_plan"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String,nullable=False)
    persona = _sql.Column(_sql.String)
    profile_img = _sql.Column(_sql.String)
    visible_for = _sql.Column(_sql.Enum(VisibleForEnum), nullable=False)
    description = _sql.Column(_sql.String)
    org_id=_sql.Column(_sql.Integer)
    carbs=_sql.Column(_sql.Float)
    fats=_sql.Column(_sql.Float)
    protein=_sql.Column(_sql.Float)
    created_by = _sql.Column(_sql.Integer)
    updated_by =_sql.Column(_sql.Integer)
    created_at =_sql.Column(_sql.DateTime, default=_dt.datetime.now())
    updated_at =_sql.Column(_sql.DateTime, default=_dt.datetime.now())
    is_deleted =_sql.Column(_sql.Boolean, default=False)
    
    
class Meal(_database.Base):
    __tablename__ = "meal"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    meal_time = _sql.Column(_sql.Enum(MealTimeEnum), nullable=True)
    meal_plan_id = _sql.Column(_sql.Integer)
    food_id = _sql.Column(_sql.Integer)
    quantity = _sql.Column(_sql.Float)
    created_by = _sql.Column(_sql.Integer, nullable=True)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    updated_by = _sql.Column(_sql.Integer, nullable=True)
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now(), onupdate=_dt.datetime.now())
    is_deleted = _sql.Column(_sql.Boolean, default=False)
    
class MemberMealPlan(_database.Base):
    __tablename__ = "member_meal_plan"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    member_id = _sql.Column(_sql.Integer)
    meal_plan_id = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean, default=False)