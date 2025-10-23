"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.project import Project
from app.models.instructor import Instructor


class TestProjectEndpoints:
    """Test project-related endpoints."""
    
    def test_create_project(self, client: TestClient, db: Session, sample_project_data):
        """Test project creation."""
        response = client.post("/api/v1/projects/", json=sample_project_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_project_data["title"]
        assert data["project_type"] == sample_project_data["project_type"]
    
    def test_get_projects(self, client: TestClient, db: Session):
        """Test getting projects list."""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_project_by_id(self, client: TestClient, db: Session, sample_project_data):
        """Test getting project by ID."""
        # First create a project
        create_response = client.post("/api/v1/projects/", json=sample_project_data)
        project_id = create_response.json()["id"]
        
        # Then get it
        response = client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id


class TestInstructorEndpoints:
    """Test instructor-related endpoints."""
    
    def test_create_instructor(self, client: TestClient, db: Session, sample_instructor_data):
        """Test instructor creation."""
        response = client.post("/api/v1/instructors/", json=sample_instructor_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_instructor_data["name"]
        assert data["email"] == sample_instructor_data["email"]
    
    def test_get_instructors(self, client: TestClient, db: Session):
        """Test getting instructors list."""
        response = client.get("/api/v1/instructors/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestClassroomEndpoints:
    """Test classroom-related endpoints."""
    
    def test_create_classroom(self, client: TestClient, db: Session, sample_classroom_data):
        """Test classroom creation."""
        response = client.post("/api/v1/classrooms/", json=sample_classroom_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_classroom_data["name"]
        assert data["capacity"] == sample_classroom_data["capacity"]
    
    def test_seed_default_classrooms(self, client: TestClient, db: Session):
        """Test seeding default classrooms."""
        response = client.post("/api/v1/classrooms/seed-default")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestAlgorithmEndpoints:
    """Test algorithm-related endpoints."""
    
    def test_get_algorithms(self, client: TestClient):
        """Test getting available algorithms."""
        response = client.get("/api/v1/algorithms/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_run_algorithm(self, client: TestClient):
        """Test running an algorithm."""
        algorithm_data = {
            "algorithm_type": "greedy",
            "parameters": {}
        }
        response = client.post("/api/v1/algorithms/run", json=algorithm_data)
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
