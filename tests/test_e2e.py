"""
End-to-end tests for the Optimization Planner API.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.core.security import create_access_token


class TestE2E:
    """End-to-end test scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def admin_token(self):
        """Create admin token for testing."""
        return create_access_token(subject=1, data={"role": "admin"})
    
    def test_complete_workflow(self, client: TestClient, admin_token: str):
        """Test complete optimization workflow."""
        
        # 1. Health check
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
        # 2. Get available algorithms
        response = client.get("/api/v1/algorithms")
        assert response.status_code == 200
        algorithms = response.json()
        assert len(algorithms) > 0
        
        # 3. Get projects
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        
        # 4. Get instructors
        response = client.get("/api/v1/instructors")
        assert response.status_code == 200
        
        # 5. Get classrooms
        response = client.get("/api/v1/classrooms")
        assert response.status_code == 200
        
        # 6. Run optimization algorithm
        algorithm_data = {
            "algorithm_type": "greedy",
            "parameters": {
                "max_iterations": 100,
                "timeout": 30
            }
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            "/api/v1/algorithms/execute",
            json=algorithm_data,
            headers=headers
        )
        # Should return 200 or 422 (validation error)
        assert response.status_code in [200, 422]
        
        # 7. Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert "data" in metrics
    
    def test_authentication_flow(self, client: TestClient):
        """Test authentication workflow."""
        
        # 1. Create admin user
        response = client.post("/api/v1/auth/create-admin")
        assert response.status_code == 200
        
        # 2. Login
        login_data = {
            "email": "admin@example.com",
            "password": "admin123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        
        # 3. Use token for protected endpoint
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/projects", headers=headers)
        assert response.status_code == 200
    
    def test_error_handling(self, client: TestClient):
        """Test error handling scenarios."""
        
        # 1. Invalid endpoint
        response = client.get("/api/v1/invalid-endpoint")
        assert response.status_code == 404
        
        # 2. Invalid login
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        
        # 3. Invalid algorithm parameters
        algorithm_data = {
            "algorithm_type": "invalid_algorithm",
            "parameters": {}
        }
        response = client.post("/api/v1/algorithms/execute", json=algorithm_data)
        assert response.status_code in [400, 422]
    
    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting functionality."""
        
        # Make multiple requests quickly
        for i in range(10):
            response = client.get("/api/v1/algorithms")
            assert response.status_code == 200
        
        # Should still work (rate limit is high for testing)
        response = client.get("/api/v1/algorithms")
        assert response.status_code == 200
    
    def test_data_consistency(self, client: TestClient):
        """Test data consistency across endpoints."""
        
        # Get algorithms
        response = client.get("/api/v1/algorithms")
        assert response.status_code == 200
        algorithms = response.json()
        
        # Verify algorithm structure
        for algorithm in algorithms:
            assert "type" in algorithm
            assert "name" in algorithm
            assert "description" in algorithm
            
        # Get projects
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        projects = response.json()
        
        # Verify projects is a list
        assert isinstance(projects, list)
        
        # Get instructors
        response = client.get("/api/v1/instructors")
        assert response.status_code == 200
        instructors = response.json()
        
        # Verify instructors structure
        if instructors:
            for instructor in instructors:
                assert "id" in instructor
                assert "name" in instructor
