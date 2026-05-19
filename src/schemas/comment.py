from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    comment_text: str = Field(min_length=1, max_length=255)

class CommentResponse(BaseModel):
    id: int
    comment_text: str
    created_at: datetime
    updated_at: datetime
    user_id: int
    photo_id: int

    model_config = ConfigDict(from_attributes=True)