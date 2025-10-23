def test_create_instructor(client, admin_token, db):
    """Öğretim elemanı oluşturma testi"""
    response = client.post(
        "/api/v1/instructors/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "type": "professor",
            "department": "Computer Engineering",
            "user_id": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "professor"
    assert data["department"] == "Computer Engineering"

def test_create_instructor_unauthorized(client, instructor_token):
    """Yetkisiz öğretim elemanı oluşturma testi"""
    response = client.post(
        "/api/v1/instructors/",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={
            "type": "professor",
            "department": "Computer Engineering",
            "user_id": 1
        }
    )
    assert response.status_code == 403

def test_read_instructors(client, admin_token):
    """Öğretim elemanlarını listeleme testi"""
    response = client.get(
        "/api/v1/instructors/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_read_instructor(client, admin_token):
    """Belirli bir öğretim elemanını getirme testi"""
    response = client.get(
        "/api/v1/instructors/1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

def test_update_instructor(client, admin_token):
    """Öğretim elemanı güncelleme testi"""
    response = client.put(
        "/api/v1/instructors/1",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "department": "Updated Department",
            "final_project_count": 2
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "Updated Department"
    assert data["final_project_count"] == 2

def test_delete_instructor(client, admin_token):
    """Öğretim elemanı silme testi"""
    # Önce yeni bir öğretim elemanı oluştur
    create_response = client.post(
        "/api/v1/instructors/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "type": "research_assistant",
            "department": "Test Department",
            "user_id": 2
        }
    )
    instructor_id = create_response.json()["id"]
    
    # Oluşturulan öğretim elemanını sil
    response = client.delete(
        f"/api/v1/instructors/{instructor_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204
    
    # Silinen öğretim elemanını kontrol et
    get_response = client.get(
        f"/api/v1/instructors/{instructor_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == 404 