
import pydantic
import datetime
from datetime import date
from typing import Optional
from enum import Enum as PyEnum

class FoodBase(pydantic.BaseModel):
    org_id: int
    name: str
    brand: Optional[str] = None
    category: str
    description: Optional[str] = None
    other_name: Optional[str] = None
    total_nutrition: float
    kcal: float
    protein: float
    fat: float
    carbohydrates: float
    carbs_sugar: Optional[float] = None
    carbs_saturated: Optional[float] = None
    kilojoules: Optional[float] = None
    fiber: Optional[float] = None
    calcium: Optional[float] = None
    iron: Optional[float] = None
    magnesium: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    sodium: Optional[float] = None
    zinc: Optional[float] = None
    copper: Optional[float] = None
    selenium: Optional[float] = None
    vitamin_a: Optional[float] = None
    vitamin_b1: Optional[float] = None
    vitamin_b2: Optional[float] = None
    vitamin_b6: Optional[float] = None
    vitamin_b12: Optional[float] = None
    vitamin_c: Optional[float] = None
    vitamin_d: Optional[float] = None
    vitamin_e: Optional[float] = None
    folic_acid: Optional[float] = None
    fat_unsaturated: Optional[float] = None
    cholesterol: Optional[float] = None
    alcohol: Optional[float] = None
    alchohol_mono: Optional[float] = None
    alchohol_poly: Optional[float] = None
    trans_fat: Optional[float] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None

    class Config:
        from_attribute = True
        extra = "forbid"

class FoodCreate(FoodBase):
    created_at: Optional[datetime.datetime] = datetime.datetime.now()
    created_by: Optional[int] = None

    class Config:
        from_attribute = True

class FoodRead(FoodBase):
    id: int
    created_at: Optional[datetime.datetime]
    created_by: Optional[int] = None

    class Config:
        from_attribute = True


class FoodUpdate(pydantic.BaseModel):
    id: int
    org_id: Optional[int] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    other_name: Optional[str] = None
    total_nutrition: Optional[float] = None
    kcal: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbohydrates: Optional[float] = None
    carbs_sugar: Optional[float] = None
    carbs_saturated: Optional[float] = None
    kilojoules: Optional[float] = None
    fiber: Optional[float] = None
    calcium: Optional[float] = None
    iron: Optional[float] = None
    magnesium: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None
    sodium: Optional[float] = None
    zinc: Optional[float] = None
    copper: Optional[float] = None
    selenium: Optional[float] = None
    vitamin_a: Optional[float] = None
    vitamin_b1: Optional[float] = None
    vitamin_b2: Optional[float] = None
    vitamin_b6: Optional[float] = None
    vitamin_b12: Optional[float] = None
    vitamin_c: Optional[float] = None
    vitamin_d: Optional[float] = None
    vitamin_e: Optional[float] = None
    folic_acid: Optional[float] = None
    fat_unsaturated: Optional[float] = None
    cholesterol: Optional[float] = None
    alcohol: Optional[float] = None
    alchohol_mono: Optional[float] = None
    alchohol_poly: Optional[float] = None
    trans_fat: Optional[float] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    updated_at: Optional[datetime.datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attribute = True


class CategoryEnum(str, PyEnum):
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

class FoodFilterParams(pydantic.BaseModel):
    search_key: Optional[str] = None
    category: Optional[str] = None
    total_nutrition: Optional[int] = None
    total_fat: Optional[int] = None
    sort_key:Optional[str]=None
    sort_order: Optional[str] = "desc"
    limit: Optional[int] = None
    offset: Optional[int] = None

class FoodListResponse(pydantic.BaseModel):
    id: Optional[int] = 0
    name: Optional[str] = None

class FoodCreateResponse(pydantic.BaseModel):
    id: int
    org_id: int
    created_at: Optional[datetime.datetime]
    created_by: Optional[int] = None

    class Config:
        from_attribute = True