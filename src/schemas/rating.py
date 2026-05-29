from pydantic import BaseModel, Field


class RatingModel(BaseModel):
    value: int = Field(ge=1, le=5, description="Оцінка від 1 до 5 зірок")

class RatingResponse(BaseModel):
    id: int
    value: int  
    photo_id: int
    user_id: int

    class Config:
        from_attributes = True