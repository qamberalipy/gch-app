
import pydantic
import datetime
from datetime import date
from typing import Optional


class FoodBase(pydantic.BaseModel):
    org_id: int
    name: str
    brand: Optional[str]
    category: str
    description: Optional[str]
    other_name: Optional[str]
    total_nutrition: float
    kcal: float
    protein: float
    fat: float
    carbohydrates: float
    carbs_sugar: Optional[float]
    carbs_saturated: Optional[float]
    kilojoules: Optional[float]
    fiber: Optional[float]
    calcium: Optional[float]
    iron: Optional[float]
    magnesium: Optional[float]
    phosphorus: Optional[float]
    potassium: Optional[float]
    sodium: Optional[float]
    zinc: Optional[float]
    copper: Optional[float]
    selenium: Optional[float]
    vitamin_a: Optional[float]
    vitamin_b1: Optional[float]
    vitamin_b2: Optional[float]
    vitamin_b6: Optional[float]
    vitamin_b12: Optional[float]
    vitamin_c: Optional[float]
    vitamin_d: Optional[float]
    vitamin_e: Optional[float]
    folic_acid: Optional[float]
    fat_unsaturated: Optional[float]
    cholesterol: Optional[float]
    alcohol: Optional[float]
    alchohol_mono: Optional[float]
    alchohol_poly: Optional[float]
    trans_fat: Optional[float]
    weight: Optional[float]
    weight_unit: Optional[str]

    class Config:
        from_attribute = True

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


class FoodCreateResponse(pydantic.BaseModel):
    id: int
    org_id: int
    created_at: Optional[datetime.datetime]
    created_by: Optional[int] = None

    class Config:
        from_attribute = True