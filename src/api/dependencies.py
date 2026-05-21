from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.database import get_db
from src.db.models import Role, User
from src.repository.users import get_user_by_email

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """Декодує токен і повертає поточного користувача."""
    token = credentials.credentials 
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
        if payload.get("scope") != "access_token":
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid scope for the token"
            )
            
    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(email, db)
    if user is None or not user.is_active:
        raise credentials_exception
        
    return user

async def get_current_admin(current_user: User = Depends(get_current_user)):
    """Перевіряє, чи є поточний користувач адміністратором."""
    if current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions. Admin access required."
        )
    return current_user

async def get_current_moderator(current_user: User = Depends(get_current_user)):
    """Перевіряє, чи є поточний користувач модератором АБО адміністратором."""
    if current_user.role not in [Role.admin, Role.moderator]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions. Moderator access required."
        )
    return current_user

class RoleChecker:
    """
    Клас-залежність для перевірки прав доступу.
    Дозволяє пускати на маршрут лише користувачів із вказаними ролями.
    """
    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have enough permissions to perform this action"
            )
        return current_user