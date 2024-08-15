import datetime as _dt
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative
from enum import Enum as PyEnum


class  FoodVisibleFor(PyEnum):
    only_me="Only me"
    members="Members in my gym"
    coaches_and_staff="Coaches and Staff in my gym" 
    everyone="Everyone in my gym"

class CategoryEnum(PyEnum):
    baked_products = "Baked Products"
    beverages = "Beverages"
    cheese_eggs = "Cheese Milk and Eggs Products"
    cooked_meals = "Cooked Meals"
    fish_products = "Fish Products"
    fruits_vegs = "Fruits and Vegetables"
    herbs_spices = "Herbs and Spices"
    meat_products = "Meat Products"
    nuts_seeds_snacks = "Nuts Seeds and Snacks"
    pasta_cereals = "Pasta and Breakfast Cereals"
    restaurant_meals = "Restaurant Meals"
    soups_sauces = "Soups, Sauces, fats and oil"
    sweets_candy = "Sweets and Candy"
    other = "Other"

class WeightUnitEnum(PyEnum):
    g = "Gram"
    ml = "ml"
    g_ml = "Gram/ML"

class Food(_database.Base):
    __tablename__ = "foods"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    org_id = _sql.Column(_sql.Integer)
    name = _sql.Column(_sql.String, nullable=False)
    brand = _sql.Column(_sql.String)
    category = _sql.Column(_sql.Enum(CategoryEnum))
    description = _sql.Column(_sql.String)
    img_url=_sql.Column(_sql.String)
    visible_for = _sql.Column(_sql.Enum(FoodVisibleFor))
    other_name = _sql.Column(_sql.String)
    total_nutrition = _sql.Column(_sql.Float)
    kcal = _sql.Column(_sql.Float)
    protein = _sql.Column(_sql.Float)
    fat = _sql.Column(_sql.Float)
    carbohydrates = _sql.Column(_sql.Float)
    carbs_sugar = _sql.Column(_sql.Float)
    carbs_saturated = _sql.Column(_sql.Float)
    kilojoules = _sql.Column(_sql.Float)
    fiber = _sql.Column(_sql.Float)
    calcium = _sql.Column(_sql.Float)
    iron = _sql.Column(_sql.Float)
    magnesium = _sql.Column(_sql.Float)
    phosphorus = _sql.Column(_sql.Float)
    potassium = _sql.Column(_sql.Float)
    sodium = _sql.Column(_sql.Float)
    zinc = _sql.Column(_sql.Float)
    copper = _sql.Column(_sql.Float)
    selenium = _sql.Column(_sql.Float)
    vitamin_a = _sql.Column(_sql.Float)
    vitamin_b1 = _sql.Column(_sql.Float)
    vitamin_b2 = _sql.Column(_sql.Float)
    vitamin_b6 = _sql.Column(_sql.Float)
    vitamin_b12 = _sql.Column(_sql.Float)
    vitamin_c = _sql.Column(_sql.Float)
    vitamin_d = _sql.Column(_sql.Float)
    vitamin_e = _sql.Column(_sql.Float)
    folic_acid = _sql.Column(_sql.Float)
    fat_unsaturated = _sql.Column(_sql.Float)
    cholesterol = _sql.Column(_sql.Float)
    alcohol = _sql.Column(_sql.Float)
    alchohol_mono = _sql.Column(_sql.Float)
    alchohol_poly = _sql.Column(_sql.Float)
    trans_fat = _sql.Column(_sql.Float)
    weight = _sql.Column(_sql.Float)
    weight_unit = _sql.Column(_sql.Enum(WeightUnitEnum))
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now(), onupdate=_dt.datetime.now())
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean, default=False)