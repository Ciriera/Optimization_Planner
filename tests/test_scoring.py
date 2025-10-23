"""
Tests for scoring service
"""

import pytest
import tempfile
import os
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from app.services.scoring import ScoringService


class TestScoringService:
    """Test cases for Scoring service."""
    
    def test_initialization(self):
        """Test service initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the scores directory
            original_dir = ScoringService.__init__.__defaults__[0] if ScoringService.__init__.__defaults__ else None
            
            service = ScoringService()
            
            # Check if scores directory is created
            assert hasattr(service, 'scores_dir')
            assert os.path.exists(service.scores_dir)
    
    @pytest.mark.asyncio
    async def test_calculate_scores_empty(self):
        """Test calculating scores with no schedules."""
        service = ScoringService()
        db_mock = AsyncMock()
        
        # Mock empty schedules
        db_mock.execute.return_value.scalars.return_value.all.return_value = []
        
        scores = await service.calculate_scores(db_mock)
        
        assert "timestamp" in scores
        assert scores["total_schedules"] == 0
        assert "metrics" in scores
        assert "overall_score" in scores
        assert scores["overall_score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_calculate_load_balance_score(self):
        """Test load balance score calculation."""
        service = ScoringService()
        db_mock = AsyncMock()
        
        # Mock instructors
        mock_instructor1 = MagicMock()
        mock_instructor1.id = 1
        mock_instructor1.name = "Test Instructor 1"
        mock_instructor1.type = "prof"
        mock_instructor1.bitirme_count = 2
        mock_instructor1.ara_count = 1
        mock_instructor1.total_load = 3
        
        mock_instructor2 = MagicMock()
        mock_instructor2.id = 2
        mock_instructor2.name = "Test Instructor 2"
        mock_instructor2.type = "assistant"
        mock_instructor2.bitirme_count = 1
        mock_instructor2.ara_count = 2
        mock_instructor2.total_load = 3
        
        db_mock.execute.return_value.scalars.return_value.all.return_value = [
            mock_instructor1, mock_instructor2
        ]
        
        # Mock empty schedules
        schedules = []
        
        result = await service._calculate_load_balance_score(db_mock, schedules)
        
        assert "score" in result
        assert "variance" in result
        assert "mean" in result
        assert "details" in result
        assert result["mean"] == 3.0  # Average of 3 and 3
        assert result["variance"] == 0.0  # No variance
    
    def test_calculate_classroom_changes_score(self):
        """Test classroom changes score calculation."""
        service = ScoringService()
        
        # Mock schedules
        mock_schedule1 = MagicMock()
        mock_schedule1.classroom_id = 1
        mock_project1 = MagicMock()
        mock_project1.responsible_id = 1
        mock_schedule1.project = mock_project1
        
        mock_schedule2 = MagicMock()
        mock_schedule2.classroom_id = 2
        mock_project2 = MagicMock()
        mock_project2.responsible_id = 1
        mock_schedule2.project = mock_project2
        
        schedules = [mock_schedule1, mock_schedule2]
        
        result = service._calculate_classroom_changes_score(schedules)
        
        assert "score" in result
        assert "changes" in result
        assert "total_assignments" in result
        assert result["changes"] == 1  # One classroom change
        assert result["total_assignments"] == 2
    
    def test_calculate_time_efficiency_score(self):
        """Test time efficiency score calculation."""
        service = ScoringService()
        
        # Mock schedules with gaps
        mock_schedule1 = MagicMock()
        mock_schedule1.timeslot_id = 1
        mock_project1 = MagicMock()
        mock_project1.responsible_id = 1
        mock_schedule1.project = mock_project1
        
        mock_schedule2 = MagicMock()
        mock_schedule2.timeslot_id = 3  # Gap between 1 and 3
        mock_project2 = MagicMock()
        mock_project2.responsible_id = 1
        mock_schedule2.project = mock_project2
        
        schedules = [mock_schedule1, mock_schedule2]
        
        result = service._calculate_time_efficiency_score(schedules)
        
        assert "score" in result
        assert "gaps" in result
        assert "total_instructors" in result
        assert result["gaps"] == 1  # One gap between timeslots 1 and 3
    
    def test_calculate_overall_score(self):
        """Test overall score calculation."""
        service = ScoringService()
        
        metrics = {
            "load_balance": {"score": 0.8},
            "classroom_changes": {"score": 0.7},
            "time_efficiency": {"score": 0.9},
            "constraint_satisfaction": {"score": 0.85},
            "gini_coefficient": {"score": 0.6},
            "instructor_preference": {"score": 0.75}
        }
        
        overall_score = service._calculate_overall_score(metrics)
        
        assert isinstance(overall_score, float)
        assert 0 <= overall_score <= 1
    
    @pytest.mark.asyncio
    async def test_generate_score_json(self):
        """Test score.json generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create service with temp directory
            service = ScoringService()
            service.scores_dir = temp_dir
            
            db_mock = AsyncMock()
            
            # Mock empty schedules
            db_mock.execute.return_value.scalars.return_value.all.return_value = []
            
            file_path = await service.generate_score_json(db_mock)
            
            assert os.path.exists(file_path)
            assert file_path.endswith('.json')
            
            # Check that latest score.json was also created
            latest_file = os.path.join(temp_dir, "score.json")
            assert os.path.exists(latest_file)
    
    @pytest.mark.asyncio
    async def test_get_latest_scores(self):
        """Test getting latest scores."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ScoringService()
            service.scores_dir = temp_dir
            
            # Test when no file exists
            result = await service.get_latest_scores()
            assert result is None
            
            # Create a test score file
            test_scores = {
                "timestamp": "2024-01-01T00:00:00",
                "total_schedules": 5,
                "overall_score": 0.8
            }
            
            import json
            latest_file = os.path.join(temp_dir, "score.json")
            with open(latest_file, 'w') as f:
                json.dump(test_scores, f)
            
            result = await service.get_latest_scores()
            assert result is not None
            assert result["total_schedules"] == 5
            assert result["overall_score"] == 0.8
