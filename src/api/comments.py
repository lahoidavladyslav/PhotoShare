from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import Role, User
from src.repository import comments as repository_comments
from src.repository import photos as repository_photos
from src.schemas.comment import CommentCreate, CommentResponse

router = APIRouter(prefix="/comments", tags=["comments"])

@router.post("/photos/{photo_id}/comments/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    photo_id: int,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Створює новий коментар до вказаної світлини."""
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    
    new_comment = await repository_comments.create_comment(db, photo_id, current_user, body.comment_text)
    return new_comment

@router.put("/comments/{comment_id}/", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Оновлює коментар. Дозволено ТІЛЬКИ автору коментаря."""
    comment = await repository_comments.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You can only edit your own comments"
        )
        
    updated_comment = await repository_comments.update_comment(db, comment_id, body.comment_text)
    return updated_comment

@router.delete("/comments/{comment_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Видаляє коментар. 
    Дозволено автору коментаря, а також користувачам з ролями admin або moderator.
    """
    comment = await repository_comments.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        
    if comment.user_id != current_user.id and current_user.role not in [Role.admin, Role.moderator]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions to delete this comment"
        )
        
    await repository_comments.delete_comment(db, comment_id)
    return None