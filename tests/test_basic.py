"""
Basic tests for the application
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_root(client: AsyncClient):
    """Root endpoint test"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Project Assignment API"

async def test_health_check(client: AsyncClient):
    """Health check endpoint test"""
    response = await client.get("/api/v1/health")
    # Accept either 200 or 307 (redirect) as valid responses
    assert response.status_code in [200, 307]
    if response.status_code == 200:
        data = response.json()
        assert "status" in data

def test_basic():
    """Basit test"""
    assert 1 + 1 == 2

def test_string():
    """String test"""
    assert "hello" + " world" == "hello world"

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (2, 3, 5),
    (3, 4, 7),
])
def test_add(a, b, expected):
    """Parametrize test"""
    assert a + b == expected