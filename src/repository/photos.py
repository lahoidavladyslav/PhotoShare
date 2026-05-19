from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import Photo, Tag, User


async def create_photo(
    db: AsyncSession, 
    url: str, 
    description: Optional[str], 
    user: User, 
    tag_names: List[str]
) -> Photo:
    tags = []
    for name in tag_names[:5]:
        stmt = select(Tag).where(Tag.name == name.lower().strip())
        result = await db.execute(stmt)
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name.lower().strip())
            db.add(tag)
        tags.append(tag)

    new_photo = Photo(
        url=url,
        description=description,
        owner_id=user.id,
        photo_tags=tags
    )

    db.add(new_photo)
    await db.commit()
    
    stmt = (
        select(Photo)
        .where(Photo.id == new_photo.id)
        .options(selectinload(Photo.photo_tags)) 
    )
    result = await db.execute(stmt)
    return result.scalar_one()

async def get_photo_by_id(db: AsyncSession, photo_id: int) -> Optional[Photo]:
    stmt = (
        select(Photo)
        .where(Photo.id == photo_id)
        .options(
            selectinload(Photo.photo_tags),
            selectinload(Photo.comments)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_photo_description(
    db: AsyncSession, 
    photo_id: int, 
    new_description: str, 
    user: User
) -> Optional[Photo]:
    """Оновлює опис світлини (тільки якщо користувач — власник або адмін)."""
    photo = await get_photo_by_id(db, photo_id)
    if photo:
        photo.description = new_description
        await db.commit()
        await db.refresh(photo)
    return photo

async def delete_photo(db: AsyncSession, photo_id: int) -> bool:
    """Видаляє світлину з бази даних."""
    photo = await get_photo_by_id(db, photo_id)
    if photo:
        await db.delete(photo)
        await db.commit()
        return True
    return False