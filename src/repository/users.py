from libgravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash
from src.db.models import Role, User
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