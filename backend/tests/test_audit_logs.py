import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.tests.utils.user import create_random_user, authentication_token_from_email
from app.tests.utils.utils import random_lower_string
from app.crud.audit_log import create_audit_log
from app.schemas.audit_log import AuditLogCreate
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio

async def test_create_audit_log(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Denetim kaydı oluşturma testi"""
    response = await client.post(
        "/api/v1/audit-logs/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "action": "test_action",
            "details": "Test audit log",
            "ip_address": "127.0.0.1",
            "user_agent": "test-agent"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["action"] == "test_action"
    assert data["details"] == "Test audit log"
    assert data["ip_address"] == "127.0.0.1"
    assert data["user_agent"] == "test-agent"

async def test_get_audit_logs(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Denetim kayıtlarını listeleme testi"""
    # Birkaç denetim kaydı oluştur
    logs = []
    for i in range(3):
        log = AuditLog(
            action=f"test_action_{i}",
            details=f"Test audit log {i}",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        db_session.add(log)
        logs.append(log)
    await db_session.commit()

    response = await client.get(
        "/api/v1/audit-logs/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert all("action" in log for log in data)
    assert all("details" in log for log in data)

async def test_get_audit_logs_normal_user(client: AsyncClient, normal_user_token: str):
    """Normal kullanıcı denetim kayıtları erişim testi"""
    response = await client.get(
        "/api/v1/audit-logs/",
        headers={"Authorization": f"Bearer {normal_user_token}"}
    )
    assert response.status_code == 403  # Forbidden

async def test_get_audit_log(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Belirli bir denetim kaydını getirme testi"""
    # Bir denetim kaydı oluştur
    log = AuditLog(
        action="test_action",
        details="Test audit log",
        ip_address="127.0.0.1",
        user_agent="test-agent"
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    response = await client.get(
        f"/api/v1/audit-logs/{log.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "test_action"
    assert data["details"] == "Test audit log"

async def test_get_nonexistent_audit_log(client: AsyncClient, admin_token: str):
    """Var olmayan denetim kaydını getirme testi"""
    response = await client.get(
        "/api/v1/audit-logs/999999",  # Var olmayan ID
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404

async def test_count_audit_logs(client: AsyncClient, admin_token: str, db_session: AsyncSession):
    """Denetim kayıtları sayısını getirme testi"""
    # Birkaç denetim kaydı oluştur
    for i in range(3):
        log = AuditLog(
            action=f"test_action_{i}",
            details=f"Test audit log {i}",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        db_session.add(log)
    await db_session.commit()

    response = await client.get(
        "/api/v1/audit-logs/count",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert data["count"] >= 3

def test_create_audit_log(db: Session) -> None:
    """Test creating an audit log entry."""
    user = create_random_user(db)
    audit_log_in = AuditLogCreate(
        user_id=user.id,
        action="test_action",
        entity_type="test_entity",
        entity_id=1,
        details="Test details",
        ip_address="127.0.0.1"
    )
    audit_log = create_audit_log(db=db, obj_in=audit_log_in)
    assert audit_log.user_id == user.id
    assert audit_log.action == "test_action"
    assert audit_log.entity_type == "test_entity"
    assert audit_log.entity_id == 1
    assert audit_log.details == "Test details"
    assert audit_log.ip_address == "127.0.0.1"


def test_get_audit_logs(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test getting audit logs as a superuser."""
    user = create_random_user(db)
    # Create some audit logs
    for i in range(3):
        audit_log_in = AuditLogCreate(
            user_id=user.id,
            action=f"test_action_{i}",
            entity_type="test_entity",
            entity_id=i,
            details=f"Test details {i}",
            ip_address="127.0.0.1"
        )
        create_audit_log(db=db, obj_in=audit_log_in)
    
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 3
    for item in content:
        assert "id" in item
        assert "action" in item
        assert "entity_type" in item
        assert "timestamp" in item


def test_get_audit_logs_normal_user(
    client: TestClient, normal_user_token_headers: dict, db: Session
) -> None:
    """Test that normal users cannot access audit logs."""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403


def test_get_audit_log(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test getting a specific audit log entry."""
    user = create_random_user(db)
    audit_log_in = AuditLogCreate(
        user_id=user.id,
        action="test_action",
        entity_type="test_entity",
        entity_id=1,
        details="Test details",
        ip_address="127.0.0.1"
    )
    audit_log = create_audit_log(db=db, obj_in=audit_log_in)
    
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/{audit_log.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == audit_log.id
    assert content["action"] == audit_log.action
    assert content["entity_type"] == audit_log.entity_type
    assert content["entity_id"] == audit_log.entity_id


def test_get_nonexistent_audit_log(
    client: TestClient, superuser_token_headers: dict
) -> None:
    """Test getting a nonexistent audit log entry."""
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/999999",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_count_audit_logs(
    client: TestClient, superuser_token_headers: dict, db: Session
) -> None:
    """Test counting audit logs."""
    user = create_random_user(db)
    # Create some audit logs
    for i in range(3):
        audit_log_in = AuditLogCreate(
            user_id=user.id,
            action=f"test_action_{i}",
            entity_type="test_entity",
            entity_id=i,
            details=f"Test details {i}",
            ip_address="127.0.0.1"
        )
        create_audit_log(db=db, obj_in=audit_log_in)
    
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/count",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    count = response.json()
    assert count >= 3 