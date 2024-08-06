
import pydantic
from datetime import date
from typing import Dict, List, Optional
from app.Exercise.models import ExerciseType,VisibleFor,Difficulty

class ExerciseBase(pydantic.BaseModel):
    exercise_name:str
    visible_for:VisibleFor
    org_id:int
    exercise_type :ExerciseType
    difficulty:Difficulty
    sets :int
    seconds_per_set:List[int]
    repetitions_per_set:List[int] 
    rest_between_set:List[int]  
    distance:float
    speed:float
    met_id :int
    gif_url :str
    video_url_male :str 
    video_url_female :str
    thumbnail_male :str 
    thumbnail_female :str
    image_url_female :str
    image_url_male :str 

    class Config:
            from_attributes = True

class Category(pydantic.BaseModel):
    id:int 
    category_name:str

class Met(pydantic.BaseModel):
    id:int 
    met_value:str

class ExerciseFilterParams(pydantic.BaseModel):
    search_key: Optional[str] = None
    category : Optional[int] = None
    equipment : Optional[List[int]] = []
    primary_muscle: Optional[List[int]] = []
    sort_key: Optional[str] = None
    sort_order: Optional[str] = 'asc'
    limit:Optional[int] = None
    offset:Optional[int] = None

class ExerciseCreate(ExerciseBase):
    category_id:int
    equipment_ids:Optional[List[int]]
    primary_muscle_ids:Optional[List[int]]
    secondary_muscle_ids:Optional[List[int]]
    primary_joint_ids:Optional[List[int]]   
    created_by:int
    updated_by:int

class ExerciseRead(ExerciseBase):
    id:int
    category_name:str
    equipments:Optional[List[Dict]]
    primary_muscles:Optional[List[Dict]]
    secondary_muscles:Optional[List[Dict]]
    primary_joints:Optional[List[Dict]]   

class ExerciseUpdate(pydantic.BaseModel):
    id:int
    exercise_name:str
    visible_for:VisibleFor
    org_id:int
    category_id :int
    exercise_type :ExerciseType
    difficulty:Difficulty
    sets :int
    seconds_per_set:List[int]
    repetitions_per_set:List[int] 
    rest_between_set:List[int]  
    distance:float
    speed:float
    met_id :int
    gif_url :str
    video_url_male :str 
    video_url_female :str
    thumbnail_male :str 
    thumbnail_female :str
    image_url_female :str
    image_url_male :str 
    equipment_ids:Optional[List[int]]
    primary_muscle_ids:Optional[List[int]]
    secondary_muscle_ids:Optional[List[int]]
    primary_joint_ids:Optional[List[int]]   
    updated_by:int
    class Config:
        from_attributes = True


class Muscle(pydantic.BaseModel):
    id:int           
    muscle_name:str
    class Config:
            from_attributes = True

class Equipments(pydantic.BaseModel):
    id:int           
    equipment_name:str
    class Config:
            from_attributes = True

class PrimaryJoint(pydantic.BaseModel):
    id:int           
    joint_name:str
    class Config:
            from_attributes = True


class ExerciseDelete(pydantic.BaseModel):
    exercise_id:int
    equipment_ids:Optional[int]=None
    primary_muscle_ids:Optional[int]=None
    secondary_muscle_ids:Optional[int]=None
    primary_joint_ids:Optional[int]=None

