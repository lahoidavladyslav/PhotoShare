from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Comment, Role, User
from src.repository.comments import (
    create_comment,
    delete_comment,
    get_comments_for_photo,
    update_comment,
)


@pytest.mark.asyncio
async def test_create_comment():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_user = User(id=1, username="test_user", role=Role.user)
    photo_id = 10
    comment_text = "Дуже гарна світлина!"

    result = await create_comment(db=mock_session, photo_id=photo_id, user=mock_user, comment_text=comment_text)

    assert result.comment_text == comment_text
    assert result.photo_id == photo_id
    assert result.user_id == mock_user.id
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_comment_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_comment = Comment(id=1, comment_text="Тест", user_id=1, photo_id=1)
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_comment))

    result = await delete_comment(db=mock_session, comment_id=1)

    assert result is True
    mock_session.delete.assert_called_once_with(mock_comment)
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_comment_not_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

    result = await delete_comment(db=mock_session, comment_id=999)

    assert result is False
    mock_session.delete.assert_not_called()

@pytest.mark.asyncio
async def test_get_comments_for_photo():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_comment = Comment(id=1, comment_text="Test", user_id=1, photo_id=10)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_comment]
    mock_session.execute.return_value = mock_result

    result = await get_comments_for_photo(mock_session, photo_id=10, skip=0, limit=10)

    assert len(result) == 1
    assert result[0].photo_id == 10

@pytest.mark.asyncio
async def test_update_comment_success():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_user = User(id=1, role=Role.user)
    mock_comment = Comment(id=1, comment_text="Old text", user_id=1, photo_id=1)
    
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_comment))

    result = await update_comment(mock_session, comment_id=1, new_text="New text", user=mock_user)

    assert result.comment_text == "New text"
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_comment_forbidden():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_user = User(id=2, role=Role.user)
    mock_comment = Comment(id=1, comment_text="Old text", user_id=1, photo_id=1)
    
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_comment))

    result = await update_comment(mock_session, comment_id=1, new_text="New text", user=mock_user)

    assert result == "forbidden"
    mock_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_update_comment_not_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_user = User(id=1, role=Role.user)
    
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))

    result = await update_comment(mock_session, comment_id=999, new_text="New text", user=mock_user)

    assert result is None