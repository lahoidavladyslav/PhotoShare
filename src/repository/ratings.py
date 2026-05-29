from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Photo, Rating, User


async def create_rate(photo_id: int, value: int, user: User, db: AsyncSession):
    photo_stmt = select(Photo).where(Photo.id == photo_id)
    result = await db.execute(photo_stmt)
    photo = result.scalar_one_or_none()

    if not photo:
        return {"error": "Photo not found"}
    
    if photo.owner_id == user.id:
        return {"error": "You cannot rate your own photo"}

    rate_stmt = select(Rating).where(
        and_(Rating.photo_id == photo_id, Rating.user_id == user.id)
    )
    result = await db.execute(rate_stmt)
    if result.scalar_one_or_none():
        return {"error": "You have already rated this photo"}

    new_rate = Rating(value=value, photo_id=photo_id, user_id=user.id)
    db.add(new_rate)
    await db.flush() 
    
    avg_stmt = select(func.avg(Rating.value)).where(Rating.photo_id == photo_id)
    avg_result = await db.execute(avg_stmt)
    new_average = avg_result.scalar() or 0.0
    
    photo.average_rating = round(new_average, 2)
    
    await db.commit()
    await db.refresh(new_rate)
    
    return new_rate


async def remove_rate(rating_id: int, db: AsyncSession):
    """Видалення оцінки з бази даних та перерахунок середнього балу."""
    stmt = select(Rating).where(Rating.id == rating_id)
    result = await db.execute(stmt)
    rating = result.scalar_one_or_none()
    
    if rating:
        photo_id = rating.photo_id
        
        await db.delete(rating)
        await db.flush() 
        
        avg_stmt = select(func.avg(Rating.value)).where(Rating.photo_id == photo_id)
        avg_result = await db.execute(avg_stmt)
        new_average = avg_result.scalar() or 0.0 
        
        photo_stmt = select(Photo).where(Photo.id == photo_id)
        photo_result = await db.execute(photo_stmt)
        photo = photo_result.scalar_one()
        photo.average_rating = round(new_average, 2)
        
        await db.commit()
        return True
        
    return False