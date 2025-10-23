"""
Test suite for algorithm recommendation system
Proje açıklamasına göre: "En uygun algoritmayı öner" özelliği testleri
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.recommendation_service import RecommendationService
from app.models.algorithm import AlgorithmType


class TestRecommendationService:
    """Test cases for RecommendationService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def recommendation_service(self, mock_db):
        """RecommendationService instance with mocked database"""
        return RecommendationService(mock_db)
    
    def test_recommend_algorithm_small_dataset(self, recommendation_service, mock_db):
        """Test algorithm recommendation for small dataset"""
        problem_data = {
            "projects": [
                {"id": 1, "type": "ara", "title": "Project 1"},
                {"id": 2, "type": "ara", "title": "Project 2"}
            ],
            "instructors": [
                {"id": 1, "name": "Instructor 1", "role": "instructor"},
                {"id": 2, "name": "Instructor 2", "role": "instructor"}
            ],
            "classrooms": [
                {"id": 1, "name": "Classroom 1", "capacity": 20}
            ],
            "timeslots": [
                {"id": 1, "start_time": "09:00", "end_time": "10:00"}
            ]
        }
        
        # Mock user history
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.return_value = {"algorithm_performance": {}}
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Small dataset should favor simplex or greedy algorithms
            assert result["recommended_algorithm"] in ["simplex", "greedy"]
            assert result["confidence_score"] > 0
            assert "reasoning" in result
    
    def test_recommend_algorithm_large_dataset(self, recommendation_service, mock_db):
        """Test algorithm recommendation for large dataset"""
        problem_data = {
            "projects": [{"id": i, "type": "ara", "title": f"Project {i}"} for i in range(20)],
            "instructors": [{"id": i, "name": f"Instructor {i}", "role": "instructor"} for i in range(10)],
            "classrooms": [{"id": i, "name": f"Classroom {i}", "capacity": 20} for i in range(5)],
            "timeslots": [{"id": i, "start_time": "09:00", "end_time": "10:00"} for i in range(10)]
        }
        
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.return_value = {"algorithm_performance": {}}
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Large dataset should favor NSGA-II or hybrid algorithms
            assert result["recommended_algorithm"] in ["nsga_ii", "hybrid_cp_sat_nsga"]
            assert result["confidence_score"] > 0
    
    def test_recommend_algorithm_bitirme_projects(self, recommendation_service, mock_db):
        """Test algorithm recommendation with bitirme projects"""
        problem_data = {
            "projects": [
                {"id": 1, "type": "bitirme", "title": "Bitirme Project 1"},
                {"id": 2, "type": "bitirme", "title": "Bitirme Project 2"}
            ],
            "instructors": [
                {"id": 1, "name": "Instructor 1", "role": "instructor"},
                {"id": 2, "name": "Instructor 2", "role": "instructor"},
                {"id": 3, "name": "Instructor 3", "role": "instructor"}
            ],
            "classrooms": [{"id": 1, "name": "Classroom 1", "capacity": 20}],
            "timeslots": [{"id": 1, "start_time": "09:00", "end_time": "10:00"}]
        }
        
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.return_value = {"algorithm_performance": {}}
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Bitirme projects require strict constraints, should favor constraint-satisfying algorithms
            assert result["recommended_algorithm"] in ["cp_sat", "hybrid_cp_sat_nsga", "lexicographic"]
            assert result["confidence_score"] > 0
    
    def test_recommend_algorithm_makeup_session(self, recommendation_service, mock_db):
        """Test algorithm recommendation for makeup session"""
        problem_data = {
            "projects": [{"id": 1, "type": "ara", "title": "Project 1"}],
            "instructors": [{"id": 1, "name": "Instructor 1", "role": "instructor"}],
            "classrooms": [{"id": 1, "name": "Classroom 1", "capacity": 20}],
            "timeslots": [{"id": 1, "start_time": "09:00", "end_time": "10:00"}],
            "is_makeup": True
        }
        
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.return_value = {"algorithm_performance": {}}
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Makeup session should favor fast algorithms
            assert result["recommended_algorithm"] in ["greedy", "simplex"]
            assert result["confidence_score"] > 0
    
    def test_user_history_affects_recommendation(self, recommendation_service, mock_db):
        """Test that user history affects algorithm recommendation"""
        problem_data = {
            "projects": [{"id": 1, "type": "ara", "title": "Project 1"}],
            "instructors": [{"id": 1, "name": "Instructor 1", "role": "instructor"}],
            "classrooms": [{"id": 1, "name": "Classroom 1", "capacity": 20}],
            "timeslots": [{"id": 1, "start_time": "09:00", "end_time": "10:00"}]
        }
        
        # Mock successful user history with genetic algorithm
        user_history = {
            "algorithm_performance": {
                AlgorithmType.GENETIC_ALGORITHM: {
                    "total_runs": 10,
                    "successful_runs": 9,
                    "avg_score": 0.85,
                    "scores": [0.8, 0.9, 0.85, 0.87, 0.82]
                }
            }
        }
        
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.return_value = user_history
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Should boost genetic algorithm score due to user's success
            assert result["recommended_algorithm"] == "genetic_algorithm"
            assert result["confidence_score"] > 0.7
    
    def test_fallback_recommendation_on_error(self, recommendation_service, mock_db):
        """Test fallback recommendation when error occurs"""
        problem_data = {
            "projects": [],
            "instructors": [],
            "classrooms": [],
            "timeslots": []
        }
        
        # Mock error in user history
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.side_effect = Exception("Database error")
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Should fallback to greedy algorithm
            assert result["recommended_algorithm"] == "greedy"
            assert result["confidence_score"] == 0.5
            assert "Fallback recommendation" in result["reasoning"]
    
    def test_problem_analysis_accuracy(self, recommendation_service, mock_db):
        """Test problem analysis accuracy"""
        problem_data = {
            "projects": [{"id": 1, "type": "bitirme", "title": "Project 1"}],
            "instructors": [{"id": 1, "name": "Instructor 1", "role": "instructor"}],
            "classrooms": [{"id": 1, "name": "Classroom 1", "capacity": 20}],
            "timeslots": [{"id": 1, "start_time": "09:00", "end_time": "10:00"}]
        }
        
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.return_value = {"algorithm_performance": {}}
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Check problem analysis
            analysis = result["problem_analysis"]
            assert analysis["project_count"] == 1
            assert analysis["instructor_count"] == 1
            assert analysis["classroom_count"] == 1
            assert analysis["timeslot_count"] == 1
            assert analysis["bitirme_project_count"] == 1
            assert analysis["ara_project_count"] == 0
            assert analysis["has_strict_constraints"] == True  # Bitirme project
            assert analysis["requires_multi_objective"] == True  # Bitirme project
    
    def test_algorithm_scores_calculation(self, recommendation_service, mock_db):
        """Test algorithm scores calculation"""
        problem_data = {
            "projects": [{"id": 1, "type": "ara", "title": "Project 1"}],
            "instructors": [{"id": 1, "name": "Instructor 1", "role": "instructor"}],
            "classrooms": [{"id": 1, "name": "Classroom 1", "capacity": 20}],
            "timeslots": [{"id": 1, "start_time": "09:00", "end_time": "10:00"}]
        }
        
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.return_value = {"algorithm_performance": {}}
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Check that all algorithms have scores
            all_scores = result["all_scores"]
            assert len(all_scores) > 0
            
            # Check that recommended algorithm has highest score
            recommended = result["recommended_algorithm"]
            recommended_score = all_scores[recommended]
            
            for algo, score in all_scores.items():
                assert score <= recommended_score or score == recommended_score
    
    def test_multi_objective_optimization_detection(self, recommendation_service, mock_db):
        """Test multi-objective optimization requirement detection"""
        # Test case 1: Multiple instructors (>3)
        problem_data = {
            "projects": [{"id": 1, "type": "ara", "title": "Project 1"}],
            "instructors": [{"id": i, "name": f"Instructor {i}", "role": "instructor"} for i in range(5)],
            "classrooms": [{"id": 1, "name": "Classroom 1", "capacity": 20}],
            "timeslots": [{"id": 1, "start_time": "09:00", "end_time": "10:00"}]
        }
        
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.return_value = {"algorithm_performance": {}}
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Should require multi-objective optimization
            assert result["problem_analysis"]["requires_multi_objective"] == True
    
    def test_reasoning_generation(self, recommendation_service, mock_db):
        """Test reasoning generation for recommendations"""
        problem_data = {
            "projects": [{"id": 1, "type": "ara", "title": "Project 1"}],
            "instructors": [{"id": 1, "name": "Instructor 1", "role": "instructor"}],
            "classrooms": [{"id": 1, "name": "Classroom 1", "capacity": 20}],
            "timeslots": [{"id": 1, "start_time": "09:00", "end_time": "10:00"}]
        }
        
        with patch.object(recommendation_service, '_get_user_history') as mock_history:
            mock_history.return_value = {"algorithm_performance": {}}
            
            result = recommendation_service.recommend_algorithm(1, problem_data)
            
            # Check reasoning quality
            reasoning = result["reasoning"]
            assert len(reasoning) > 0
            assert reasoning.endswith(".")
            assert "Small problem size" in reasoning or "Medium problem size" in reasoning or "Large problem size" in reasoning


if __name__ == "__main__":
    pytest.main([__file__])
