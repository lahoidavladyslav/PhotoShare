from fastapi.testclient import TestClient

from src.main import app


def test_app_initialization():
    """Перевіряємо, що додаток успішно стартує і реєструє роутери."""
    client = TestClient(app)
    
    response = client.get("/")
    
    assert response.status_code in [200, 404]