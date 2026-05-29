from datetime import datetime, timezone

from libgravatar import Gravatar
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash
from src.db.models import BlacklistedToken, Photo, Role, User
from src.schemas.user import UserCreate


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """Шукає користувача в базі даних за його email."""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_username(username: str, db: AsyncSession) -> User | None:
    """Шукає користувача за юзернеймом (щоб уникати дублікатів)."""
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(body: UserCreate, db: AsyncSession) -> User:
    """Створює нового користувача. Перший в системі стає адміністратором."""
    stmt = select(User).limit(1)
    result = await db.execute(stmt)
    first_user = result.scalar_one_or_none()

    user_role = Role.admin if first_user is None else Role.user
    
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(f"Error generating gravatar: {e}")

    new_user = User(
        username=body.username,
        email=body.email,
        password=get_password_hash(body.password),
        role=user_role,
        avatar=avatar, 
        confirmed=False,
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

async def update_token(user: User, token: str | None, db: AsyncSession) -> None:
    """Оновлює refresh_token користувача в базі даних."""
    user.refresh_token = token
    await db.commit()
    
async def confirmed_email(email: str, db: AsyncSession) -> None:
    """Змінює статус confirmed на True для вказаного користувача."""
    user = await get_user_by_email(email, db)
    if user:
        user.confirmed = True 
        await db.commit()
        
async def get_user_profile(username: str, db: AsyncSession):
    """Отримує публічний профіль користувача та кількість його світлин."""
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return None
        
    photo_stmt = select(func.count()).select_from(Photo).where(Photo.owner_id == user.id)
    photo_result = await db.execute(photo_stmt)
    photos_count = photo_result.scalar() or 0
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "created_at": user.created_at,
        "role": user.role.value,
        "photos_count": photos_count
    }

async def add_token_to_blacklist(token: str, expires_at: datetime, db: AsyncSession):
    """Додає токен до чорного списку (Logout)."""
    expires_at_naive = expires_at.replace(tzinfo=None)
    
    blacklisted = BlacklistedToken(
        token=token, 
        expires_at=expires_at_naive,
        blacklisted_on=datetime.now(timezone.utc).replace(tzinfo=None) 
    )
    db.add(blacklisted)
    await db.commit()

async def is_token_blacklisted(token: str, db: AsyncSession) -> bool:
    """Перевіряє, чи знаходиться токен у чорному списку."""
    stmt = select(BlacklistedToken).where(BlacklistedToken.token == token)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None

async def update_user_status(username: str, is_active: bool, db: AsyncSession) -> User | None:
    """Змінює статус активності користувача (бан/розбан)."""
    user = await get_user_by_username(username, db)
    if user:
        user.is_active = is_active
        await db.commit()
        await db.refresh(user)
    return user