from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Role, User
from src.repository.users import (
    add_token_to_blacklist,
    confirmed_email,
    create_user,
    get_user_by_email,
    get_user_profile,
    is_token_blacklisted,
    update_token,
    update_user_status,
)
from src.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_get_user_by_email():
    mock_session = AsyncMock(spec=AsyncSession)
    email = "test@example.com"
    mock_user = User(id=1, email=email, username="testuser")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await get_user_by_email(email, mock_session)

    assert result is not None
    assert result.email == email
    assert result.id == 1

@pytest.mark.asyncio
@patch("src.repository.users.get_password_hash", return_value="fake_hashed_password")
async def test_create_user_first_admin(mock_get_password_hash):
    mock_session = AsyncMock(spec=AsyncSession)
    body = UserCreate(username="admin_user", email="admin@test.com", password="password123")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await create_user(body, mock_session)

    assert result.username == body.username
    assert result.role == Role.admin
    assert result.password == "fake_hashed_password" 
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_user_status():
    mock_session = AsyncMock(spec=AsyncSession)
    username = "bad_user"
    mock_user = User(id=1, username=username, is_active=True)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await update_user_status(username, False, mock_session)

    assert result.is_active is False
    mock_session.commit.assert_awaited_once()
    
@pytest.mark.asyncio
async def test_update_token():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_user = User(id=1, username="test")
    
    await update_token(mock_user, "new_token", mock_session)
    
    assert mock_user.refresh_token == "new_token"
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_confirmed_email():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_user = User(id=1, email="test@test.com", confirmed=False)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result
    
    await confirmed_email("test@test.com", mock_session)
    
    assert mock_user.confirmed is True
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_user_profile():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "test"
    mock_user.role.value = "user"
    
    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user
    
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 5
    
    mock_session.execute.side_effect = [mock_user_result, mock_count_result]
    
    result = await get_user_profile("test", mock_session)
    
    assert result is not None
    assert result["username"] == "test"
    assert result["photos_count"] == 5

@pytest.mark.asyncio
async def test_add_token_to_blacklist():
    mock_session = AsyncMock(spec=AsyncSession)
    expire_time = datetime.now(timezone.utc)
    
    await add_token_to_blacklist("bad_token", expire_time, mock_session)
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_is_token_blacklisted():
    mock_session = AsyncMock(spec=AsyncSession)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "Token Exists!"
    mock_session.execute.return_value = mock_result
    
    result = await is_token_blacklisted("bad_token", mock_session)
    
    assert result is True