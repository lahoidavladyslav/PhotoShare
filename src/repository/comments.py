from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Comment, User


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

async def get_comment_by_id(db: AsyncSession, comment_id: int) -> Comment | None:
    """Шукає коментар за його ID (потрібно для перевірки прав перед редагуванням)."""
    stmt = select(Comment).where(Comment.id == comment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_comment(db: AsyncSession, comment_id: int, new_text: str) -> Comment | None:
    """Оновлює текст коментаря."""
    comment = await get_comment_by_id(db, comment_id)
    if comment:
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