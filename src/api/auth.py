from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_current_admin,
    get_current_moderator,
    get_current_user,
)
from src.core.config import settings
from src.core.security import create_access_token, create_refresh_token, verify_password
from src.db.database import get_db
from src.db.models import User
from src.repository import users as repository_users
from src.repository.users import (
    confirmed_email,
    create_user,
    get_user_by_email,
    get_user_by_username,
    update_token,
)
from src.schemas.user import (
    RefreshTokenRequest,
    RequestEmail,
    Token,
    UserCreate,
    UserLogin,
    UserProfileResponse,
    UserResponse,
)
from src.services.email import send_email

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate, 
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Реєстрація нового користувача (Signup) з відправкою листа."""
    
    if await get_user_by_email(user_data.email, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if await get_user_by_username(user_data.username, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    new_user = await create_user(user_data, db)
    
    background_tasks.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    
    return new_user

@router.post("/login", response_model=Token)
async def login_user(
    body: UserLogin, 
    db: AsyncSession = Depends(get_db)
):
    """Вхід у систему (JSON). Можна вводити як Email, так і Username."""
    
    user = await get_user_by_email(body.username, db)
    
    if not user:
        user = await get_user_by_username(body.username, db)
    
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")

    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    await update_token(user, refresh_token, db)
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh_token", response_model=Token)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    _security: HTTPAuthorizationCredentials = Depends(security) 
):
    """
    Оновлення токенів. 
    Приймає JSON у Body ТА показує замочок у Swagger.
    """
    try:
        token = body.refresh_token 
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("scope") != "refresh_token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid scope for the token"
            )
            
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
            
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user = await get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})
    
    await update_token(user, new_refresh_token, db)
    
    return {
        "access_token": new_access_token, 
        "refresh_token": new_refresh_token, 
        "token_type": "bearer"
    }

@router.post("/request_email")
async def request_email(
    body: RequestEmail, 
    background_tasks: BackgroundTasks, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Запит на повторне відправлення листа з підтвердженням."""
    user = await get_user_by_email(body.email, db)
    
    if user and not user.confirmed:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
        
    return {"message": "Check your email for confirmation."}

@router.get("/confirmed_email/{token}")
async def confirm_email_route(token: str, db: AsyncSession = Depends(get_db)):
    """Підтвердження email за допомогою токену з листа."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")

    user = await get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
        
    if user.confirmed:
        return {"message": "Your email is already confirmed"}

    await confirmed_email(email, db)
    return {"message": "Email confirmed successfully"}

@router.get("/admin", response_model=UserResponse)
async def admin_access(current_user: User = Depends(get_current_admin)):
    """Ендпоінт для перевірки доступу адміністратора."""
    return current_user

@router.get("/moderator", response_model=UserResponse)
async def moderator_access(current_user: User = Depends(get_current_moderator)):
    """Ендпоінт для перевірки доступу модератора."""
    return current_user

@router.get("/{username}", response_model=UserProfileResponse)
async def read_user_profile(
    username: str, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отримати публічний профіль користувача за його юзернеймом."""
    profile = await repository_users.get_user_profile(username, db)
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return profile

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Вихід з системи: занулення refresh_token та блокування поточного access_token."""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        if not exp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
            
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        
        await repository_users.add_token_to_blacklist(token, expires_at, db)
        
        await repository_users.update_token(current_user, None, db)
        
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {"message": "Successfully logged out"}

@router.patch("/{username}/status", response_model=UserResponse)
async def change_user_status(
    username: str,
    is_active: bool = Query(..., description="True - активний, False - забанений"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Змінює статус користувача (Бан/Розбан). 
    Дозволено ТІЛЬКИ адміністраторам.
    """
    if current_admin.username == username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="You cannot change your own status"
        )

    user = await repository_users.update_user_status(username, is_active, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user