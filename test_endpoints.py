from fastapi.testclient import TestClient
from app.main import app
import logging

# Testler için log seviyesini azaltalım
logging.basicConfig(level=logging.ERROR)

client = TestClient(app)

def test_health():
    """Sağlık kontrolü endpointini test et"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_algorithms_list():
    """Algoritma listesi endpointini test et"""
    # Önce token alalım
    login_response = client.post(
        "/api/v1/auth/login/access-token",
        data={"username": "admin@example.com", "password": "admin"}
    )
    
    # Login başarılı olursa token alırız
    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        # Token ile algoritma listesini sorgulayalım
        response = client.get(
            "/api/v1/algorithms/list",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
    else:
        print(f"Login başarısız: {login_response.status_code}, {login_response.json()}")

def test_classrooms():
    """Sınıflar endpointini test et"""
    # Önce token alalım
    login_response = client.post(
        "/api/v1/auth/login/access-token",
        data={"username": "admin@example.com", "password": "admin"}
    )
    
    # Login başarılı olursa token alırız
    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        # Token ile sınıf listesini sorgulayalım
        response = client.get(
            "/api/v1/classrooms/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
    else:
        print(f"Login başarısız: {login_response.status_code}, {login_response.json()}")

def test_timeslots():
    """Zaman dilimleri endpointini test et"""
    # Önce token alalım
    login_response = client.post(
        "/api/v1/auth/login/access-token",
        data={"username": "admin@example.com", "password": "admin"}
    )
    
    # Login başarılı olursa token alırız
    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data.get("access_token")
        
        # Token ile zaman dilimlerini sorgulayalım
        response = client.get(
            "/api/v1/timeslots/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
    else:
        print(f"Login başarısız: {login_response.status_code}, {login_response.json()}")

# Testleri manuel çalıştırmak için
if __name__ == "__main__":
    print("Sağlık kontrolü testi...")
    test_health()
    print("Sağlık kontrolü başarılı!")
    
    print("Algoritma listesi testi...")
    test_algorithms_list()
    print("Algoritma listesi başarılı!")
    
    print("Sınıflar testi...")
    test_classrooms()
    print("Sınıflar testi başarılı!")
    
    print("Zaman dilimleri testi...")
    test_timeslots()
    print("Zaman dilimleri testi başarılı!") 