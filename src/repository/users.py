from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash
from src.db.models import User
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
    """Створює нового користувача, хешує його пароль та зберігає в БД."""
    
    hashed_password = get_password_hash(body.password)
    
    new_user = User(
        username=body.username,
        email=body.email,
        password=hashed_password,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user