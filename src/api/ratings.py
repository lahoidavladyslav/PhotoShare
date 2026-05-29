from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.api.dependencies import (
    RoleChecker,
)
from src.db.database import get_db
from src.db.models import Role, User
from src.repository import ratings as repository_ratings
from src.schemas.rating import RatingModel, RatingResponse

router = APIRouter(prefix="/ratings", tags=["ratings"])

@router.post("/{photo_id}", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def rate_photo(
    photo_id: int,
    body: RatingModel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Виставити оцінку фотографії (1-5 зірок)."""
    result = await repository_ratings.create_rate(photo_id, body.value, current_user, db)
    
    if isinstance(result, dict) and "error" in result:
        status_code = status.HTTP_400_BAD_REQUEST
        if result["error"] == "Photo not found":
            status_code = status.HTTP_404_NOT_FOUND
        
        raise HTTPException(status_code=status_code, detail=result["error"])
        
    return result

allowed_operation_for_moderators = RoleChecker([Role.admin, Role.moderator])

@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_rating(
    rating_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allowed_operation_for_moderators)
):
    """Видалити оцінку (тільки для Адміністраторів та Модераторів)."""
    success = await repository_ratings.remove_rate(rating_id, db)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
        
    return None