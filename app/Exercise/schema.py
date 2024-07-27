
import pydantic
from datetime import date
from typing import List, Optional
from app.Exercise.models import ExerciseType,VisibleFor

class ExerciseBase(pydantic.BaseModel):
    exercise_name:str
    

class ExerciseCreate(ExerciseBase):
    visible_for:VisibleFor
    category_id :int
    equipment_ids:List[int]
    primary_muscle_ids:List[int]
    secondary_muscle_ids:List[int]
    primary_joint_ids:List[int]
    exercise_type :ExerciseType
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
    created_by:int
    updated_by:int

    class Config:
        use_enum_values = True
        from_attributes = True
        
class Muscle(pydantic.BaseModel):
    id:int           
    muscle_name:str
    class Config:
            from_attributes = True

