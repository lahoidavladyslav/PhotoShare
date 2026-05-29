from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Photo, Rating, User
from src.repository.ratings import create_rate, remove_rate


@pytest.mark.asyncio
async def test_create_rate_photo_not_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    user = User(id=1)
    
    result = await create_rate(photo_id=1, value=5, user=user, db=mock_session)
    assert result == {"error": "Photo not found"}

@pytest.mark.asyncio
async def test_create_rate_own_photo():
    mock_session = AsyncMock(spec=AsyncSession)
    photo = Photo(id=1, owner_id=1)
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=photo))
    user = User(id=1)
    
    result = await create_rate(photo_id=1, value=5, user=user, db=mock_session)
    assert result == {"error": "You cannot rate your own photo"}

@pytest.mark.asyncio
async def test_create_rate_already_rated():
    mock_session = AsyncMock(spec=AsyncSession)
    photo = Photo(id=1, owner_id=2)
    existing_rating = Rating(id=1, photo_id=1, user_id=1)
    
    mock_photo_result = MagicMock(scalar_one_or_none=MagicMock(return_value=photo))
    mock_rating_result = MagicMock(scalar_one_or_none=MagicMock(return_value=existing_rating))
    mock_session.execute.side_effect = [mock_photo_result, mock_rating_result]
    
    user = User(id=1)
    
    result = await create_rate(photo_id=1, value=5, user=user, db=mock_session)
    assert result == {"error": "You have already rated this photo"}

@pytest.mark.asyncio
async def test_create_rate_success():
    mock_session = AsyncMock(spec=AsyncSession)
    photo = Photo(id=1, owner_id=2, average_rating=0.0)
    
    mock_photo_result = MagicMock(scalar_one_or_none=MagicMock(return_value=photo))
    mock_rating_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    mock_avg_result = MagicMock(scalar=MagicMock(return_value=4.5))
    
    mock_session.execute.side_effect = [mock_photo_result, mock_rating_result, mock_avg_result]
    user = User(id=1)
    
    result = await create_rate(photo_id=1, value=5, user=user, db=mock_session)
    
    assert isinstance(result, Rating)
    assert result.value == 5
    assert photo.average_rating == 4.5
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_remove_rate_not_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    
    result = await remove_rate(rating_id=1, db=mock_session)
    assert result is False
    mock_session.delete.assert_not_called()

@pytest.mark.asyncio
async def test_remove_rate_success():
    mock_session = AsyncMock(spec=AsyncSession)
    rating = Rating(id=1, photo_id=1, user_id=1, value=5)
    photo = Photo(id=1, average_rating=5.0)
    
    mock_rating_result = MagicMock(scalar_one_or_none=MagicMock(return_value=rating))
    mock_avg_result = MagicMock(scalar=MagicMock(return_value=4.0)) 
    mock_photo_result = MagicMock(scalar_one=MagicMock(return_value=photo))
    
    mock_session.execute.side_effect = [mock_rating_result, mock_avg_result, mock_photo_result]
    
    result = await remove_rate(rating_id=1, db=mock_session)
    
    assert result is True
    assert photo.average_rating == 4.0
    mock_session.delete.assert_called_once_with(rating)
    mock_session.flush.assert_awaited_once()
    mock_session.commit.assert_awaited_once()