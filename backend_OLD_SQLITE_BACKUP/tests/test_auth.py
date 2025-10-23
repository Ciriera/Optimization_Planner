import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_register_user(client: AsyncClient):
    """Kullanıcı kaydı testi"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "test123",
            "full_name": "Test User",
            "role": "instructor"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "password" not in data

async def test_login_user(client: AsyncClient):
    """Kullanıcı girişi testi"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "test123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_get_current_user(client: AsyncClient, admin_token: str):
    """Mevcut kullanıcı bilgileri testi"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@example.com"

async def test_register_duplicate_username(client: AsyncClient):
    """Aynı kullanıcı adıyla kayıt testi"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "another@example.com",
            "username": "testuser",  # Var olan kullanıcı adı
            "password": "test123",
            "full_name": "Another User",
            "role": "instructor"
        }
    )
    assert response.status_code == 400

async def test_login_wrong_password(client: AsyncClient):
    """Yanlış şifre ile giriş testi"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 401

async def test_get_current_user_invalid_token(client: AsyncClient):
    """Geçersiz token ile kullanıcı bilgileri testi"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401 