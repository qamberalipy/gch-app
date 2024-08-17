
import pydantic
from datetime import date, datetime
from typing import Dict, List, Optional
from app.Exercise.models import ExerciseType,VisibleFor,Difficulty,Intensity

class ExerciseBase(pydantic.BaseModel):
    exercise_name:str
    visible_for:VisibleFor
    org_id:int
    exercise_type :ExerciseType
    exercise_intensity:Intensity
    intensity_value:Optional[float]
    difficulty:Difficulty
    sets :Optional[int]
    seconds_per_set:Optional[List[int]]
    repetitions_per_set:Optional[List[int]] 
    rest_between_set:Optional[List[int]]  
    distance:Optional[float]
    speed:Optional[float]
    met_id :Optional[int]
    gif_url :str
    video_url_male :Optional[str] 
    video_url_female :Optional[str]
    thumbnail_male :Optional[str] 
    thumbnail_female :Optional[str]
    image_url_female :Optional[str]
    image_url_male :Optional[str] 

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
    category : Optional[List[int]] = None
    visible_for:Optional[List[VisibleFor]]=None
    difficulty:Optional[Difficulty]=None
    exercise_type:Optional[ExerciseType]=None
    sort_key: Optional[str] = None
    sort_order: Optional[str] = 'desc'
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
    category_id:int
    created_at:datetime
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
    exercise_intensity:Intensity
    intensity_value:Optional[float]
    difficulty:Difficulty
    sets :Optional[int]
    seconds_per_set:Optional[List[int]]
    repetitions_per_set:Optional[List[int]] 
    rest_between_set:Optional[List[int]]  
    distance:Optional[float]
    speed:Optional[float]
    met_id :Optional[int]
    gif_url :str
    video_url_male :Optional[str] 
    video_url_female :Optional[str]
    thumbnail_male :Optional[str] 
    thumbnail_female :Optional[str]
    image_url_female :Optional[str]
    image_url_male :Optional[str] 
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

class GetAllResponse(pydantic.BaseModel):
    data:List[ExerciseRead]
    total_counts:int
    filtered_counts:int