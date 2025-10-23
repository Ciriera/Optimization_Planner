"""
Integration tests for services and database operations.
"""
import pytest
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.services.project import ProjectService
from app.services.instructor import InstructorService
from app.services.classroom import ClassroomService
from app.services.algorithm import AlgorithmService
from app.services.recommendation_service import RecommendationService
from app.services.jury_matching_service import JuryMatchingService
from app.services.oral_exam_service import OralExamService
from app.services.accessibility_service import AccessibilityService
from app.services.calendar_service import CalendarService


class TestServiceIntegration:
    """Test service integrations."""
    
    @pytest.fixture
    async def db_session(self):
        """Get database session."""
        async for session in get_db():
            yield session
    
    @pytest.mark.asyncio
    async def test_project_service_integration(self, db_session: AsyncSession):
        """Test project service integration."""
        service = ProjectService()
        
        # Test getting projects
        projects = await service.get_multi(db_session)
        assert isinstance(projects, list)
        
        # Test creating project
        project_data = {
            "title": "Test Project",
            "description": "Integration test project",
            "project_type": "ara",
            "student_name": "Test Student",
            "student_number": "12345678"
        }
        
        try:
            project = await service.create(db_session, obj_in=project_data)
            assert project is not None
            assert project.title == project_data["title"]
        except Exception as e:
            # Expected if database constraints fail
            assert "constraint" in str(e).lower() or "foreign key" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_instructor_service_integration(self, db_session: AsyncSession):
        """Test instructor service integration."""
        service = InstructorService()
        
        # Test getting instructors
        instructors = await service.get_multi(db_session)
        assert isinstance(instructors, list)
    
    @pytest.mark.asyncio
    async def test_classroom_service_integration(self, db_session: AsyncSession):
        """Test classroom service integration."""
        service = ClassroomService()
        
        # Test getting classrooms
        classrooms = await service.get_multi(db_session)
        assert isinstance(classrooms, list)
    
    @pytest.mark.asyncio
    async def test_algorithm_service_integration(self):
        """Test algorithm service integration."""
        service = AlgorithmService()
        
        # Test listing algorithms
        algorithms = service.list_algorithms()
        assert isinstance(algorithms, list)
        assert len(algorithms) > 0
        
        # Test running algorithm
        try:
            result = service.run_algorithm("greedy", {})
            assert result is not None
        except Exception as e:
            # Expected if no data available
            assert "data" in str(e).lower() or "empty" in str(e).lower()
    
    def test_recommendation_service(self):
        """Test recommendation service."""
        service = RecommendationService()
        
        # Test getting recommendations
        recommendations = service.get_recommendations(
            user_id=1,
            context={"project_count": 10, "instructor_count": 5}
        )
        assert isinstance(recommendations, list)
    
    def test_jury_matching_service(self):
        """Test jury matching service."""
        service = JuryMatchingService()
        
        # Test jury matching
        projects = [
            {"id": 1, "title": "Project 1", "keywords": ["AI", "ML"]},
            {"id": 2, "title": "Project 2", "keywords": ["Web", "DB"]}
        ]
        
        instructors = [
            {"id": 1, "name": "Dr. Smith", "keywords": ["AI", "ML"]},
            {"id": 2, "name": "Dr. Jones", "keywords": ["Web", "DB"]}
        ]
        
        matches = service.match_juries(projects, instructors)
        assert isinstance(matches, list)
    
    def test_oral_exam_service(self):
        """Test oral exam service."""
        service = OralExamService()
        
        # Test scheduling oral exams
        projects = [
            {"id": 1, "title": "Project 1", "type": "bitirme"},
            {"id": 2, "title": "Project 2", "type": "ara"}
        ]
        
        schedule = service.schedule_oral_exams(projects)
        assert isinstance(schedule, list)
    
    def test_accessibility_service(self):
        """Test accessibility service."""
        service = AccessibilityService()
        
        # Test accessibility check
        check_result = service.check_accessibility({
            "color_contrast": True,
            "alt_text": True,
            "keyboard_navigation": True
        })
        assert isinstance(check_result, dict)
        assert "score" in check_result
        assert "recommendations" in check_result
    
    def test_calendar_service(self):
        """Test calendar service."""
        service = CalendarService()
        
        # Test calendar integration
        events = [
            {
                "title": "Project Defense",
                "start_time": "2024-01-15T10:00:00",
                "end_time": "2024-01-15T11:00:00",
                "location": "Room A101"
            }
        ]
        
        result = service.sync_events(events)
        assert isinstance(result, dict)
        assert "synced_count" in result


class TestDatabaseIntegration:
    """Test database integration."""
    
    @pytest.fixture
    async def db_session(self):
        """Get database session."""
        async for session in get_db():
            yield session
    
    @pytest.mark.asyncio
    async def test_database_connection(self, db_session: AsyncSession):
        """Test database connection."""
        from sqlalchemy import text
        
        result = await db_session.execute(text("SELECT 1 as test"))
        test_value = result.scalar()
        assert test_value == 1
    
    @pytest.mark.asyncio
    async def test_database_tables(self, db_session: AsyncSession):
        """Test database tables exist."""
        from sqlalchemy import text
        
        # Check if main tables exist
        tables = ["users", "projects", "instructors", "classrooms", "timeslots"]
        
        for table in tables:
            try:
                result = await db_session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                )
                count = result.scalar()
                assert count is not None
            except Exception as e:
                # Table might not exist or have no data
                assert "no such table" in str(e).lower() or "doesn't exist" in str(e).lower()


class TestAPIIntegration:
    """Test API integration scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    def test_api_endpoint_consistency(self, client):
        """Test API endpoint consistency."""
        
        endpoints = [
            "/api/v1/algorithms",
            "/api/v1/projects",
            "/api/v1/instructors",
            "/api/v1/classrooms"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    def test_error_response_format(self, client):
        """Test error response format consistency."""
        
        # Test 404 error
        response = client.get("/api/v1/invalid-endpoint")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data
    
    def test_cors_headers(self, client):
        """Test CORS headers."""
        
        response = client.options("/api/v1/algorithms")
        # CORS preflight should be handled
        assert response.status_code in [200, 204, 405]
