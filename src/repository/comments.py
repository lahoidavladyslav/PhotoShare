from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Comment, Role, User


async def create_comment(db: AsyncSession, photo_id: int, user: User, comment_text: str) -> Comment:
    """Створює новий коментар до фотографії."""
    new_comment = Comment(
        comment_text=comment_text,
        photo_id=photo_id,
        user_id=user.id
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment

async def get_comments_for_photo(db: AsyncSession, photo_id: int, skip: int = 0, limit: int = 10) -> Sequence[Comment]:
    """Отримує список коментарів для конкретної світлини з пагінацією."""
    stmt = select(Comment).where(Comment.photo_id == photo_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_comment_by_id(db: AsyncSession, comment_id: int) -> Comment | None:
    """Шукає коментар за його ID."""
    stmt = select(Comment).where(Comment.id == comment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_comment(db: AsyncSession, comment_id: int, new_text: str, user: User) -> Comment | None | str:
    """Оновлює текст коментаря з перевіркою прав доступу."""
    comment = await get_comment_by_id(db, comment_id)
    
    if not comment:
        return None
        
    if comment.user_id != user.id and user.role not in [Role.admin, Role.moderator]:
        return "forbidden"
        
    comment.comment_text = new_text
    await db.commit()
    await db.refresh(comment)
    return comment

async def delete_comment(db: AsyncSession, comment_id: int) -> bool:
    """Видаляє коментар."""
    comment = await get_comment_by_id(db, comment_id)
    if comment:
        await db.delete(comment)
        await db.commit()
        return True
    return False