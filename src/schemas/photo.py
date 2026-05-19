from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TagResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class PhotoResponse(BaseModel):
    id: int
    url: str
    description: Optional[str]
    created_at: datetime
    photo_tags: List[TagResponse]
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
    
class PhotoTransformModel(BaseModel):
    width: Optional[int] = 500
    height: Optional[int] = 500
    crop: Optional[str] = "fill" 
    effect: Optional[str] = "grayscale" 

class TransformResponse(BaseModel):
    original_url: str
    transformed_url: str
    qr_code_url: str