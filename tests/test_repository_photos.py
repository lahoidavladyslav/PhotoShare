from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Photo, User
from src.repository.photos import (
    create_photo,
    delete_photo,
    get_photo_by_id,
    search_photos,
    update_photo_description,
)


@pytest.mark.asyncio
async def test_get_photo_by_id():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_photo = Photo(id=1, url="http://test.com/image.jpg", description="Test")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_photo
    mock_session.execute.return_value = mock_result

    result = await get_photo_by_id(mock_session, photo_id=1)

    assert result is not None
    assert result.id == 1
    assert result.url == "http://test.com/image.jpg"

@pytest.mark.asyncio
async def test_update_photo_description():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_user = User(id=1)
    mock_photo = Photo(id=1, description="Old Description", owner_id=1)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_photo
    mock_session.execute.return_value = mock_result

    new_desc = "New Awesome Description"
    result = await update_photo_description(mock_session, 1, new_desc, mock_user)

    assert result is not None
    assert result.description == new_desc
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_photo_found():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_photo = Photo(id=1, url="http://test.com/image.jpg")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_photo
    mock_session.execute.return_value = mock_result

    result = await delete_photo(mock_session, photo_id=1)

    assert result is True
    mock_session.delete.assert_called_once_with(mock_photo)
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_photo_not_found():
    mock_session = AsyncMock(spec=AsyncSession)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await delete_photo(mock_session, photo_id=999)

    assert result is False
    mock_session.delete.assert_not_called()

@pytest.mark.asyncio
async def test_search_photos():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_photo = Photo(id=1, description="Beautiful Sea")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.unique.return_value.all.return_value = [mock_photo]
    mock_session.execute.return_value = mock_result

    result = await search_photos("Sea", skip=0, limit=10, db=mock_session)

    assert len(result) == 1
    assert result[0].description == "Beautiful Sea"
    
@pytest.mark.asyncio
async def test_create_photo():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_user = User(id=1)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    
    mock_photo_result = MagicMock()
    mock_photo_result.scalar_one.return_value = Photo(id=1, url="http://url.com", description="desc", owner_id=1)
    
    mock_session.execute.side_effect = [mock_result, mock_photo_result]

    result = await create_photo(mock_session, "http://url.com", "desc", mock_user, ["nature"])

    assert result.id == 1
    assert result.url == "http://url.com"
    mock_session.add.called
    mock_session.commit.assert_awaited_once()