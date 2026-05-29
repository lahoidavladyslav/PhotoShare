from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.main import app


@pytest.fixture
def mock_session():
    """Створює фейкову базу даних для тестів."""
    mock_db = AsyncMock(spec=AsyncSession)
    return mock_db

@pytest.fixture
def client(mock_session):
    """Створює тестовий клієнт FastAPI з підміненою базою даних."""
    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()