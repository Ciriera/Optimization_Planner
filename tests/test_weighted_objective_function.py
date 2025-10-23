"""
Test suite for weighted objective function
Proje açıklamasına göre: Total skor = (W1 * yük dengesi) + (W2 * sınıf geçişi) + (W3 * saat bütünlüğü) + (W4 * oturum minimizasyonu) + (W5 * kural uyumu)
"""

import pytest
from unittest.mock import Mock, patch

from app.services.objective_weights_service import ObjectiveWeightsService


class TestWeightedObjectiveFunction:
    """Test cases for weighted objective function calculation"""
    
    @pytest.fixture
    def weights_service(self):
        """ObjectiveWeightsService instance"""
        return ObjectiveWeightsService()
    
    def test_calculate_weighted_score_basic(self, weights_service):
        """Test basic weighted score calculation"""
        objective_scores = {
            "load_balance": 80.0,
            "classroom_changes": 70.0,
            "time_efficiency": 90.0,
            "session_minimization": 85.0,
            "rule_compliance": 95.0
        }
        
        result = weights_service.calculate_weighted_score(objective_scores)
        
        assert result["success"] == True
        assert "total_weighted_score" in result
        assert "weighted_components" in result
        assert "weights_used" in result
        assert "project_specification_formula" in result
        
        # Check that formula is correctly stated
        assert "Total skor = (W1 * yük dengesi) + (W2 * sınıf geçişi) + (W3 * saat bütünlüğü) + (W4 * oturum minimizasyonu) + (W5 * kural uyumu)" in result["project_specification_formula"]
    
    def test_calculate_weighted_score_with_custom_weights(self, weights_service):
        """Test weighted score calculation with custom weights"""
        objective_scores = {
            "load_balance": 80.0,
            "classroom_changes": 70.0,
            "time_efficiency": 90.0,
            "session_minimization": 85.0,
            "rule_compliance": 95.0
        }
        
        custom_weights = {
            "load_balance": 0.4,  # 40% weight
            "classroom_changes": 0.2,  # 20% weight
            "time_efficiency": 0.2,  # 20% weight
            "session_minimization": 0.1,  # 10% weight
            "rule_compliance": 0.1  # 10% weight
        }
        
        result = weights_service.calculate_weighted_score(objective_scores, custom_weights)
        
        assert result["success"] == True
        assert result["weights_used"] == custom_weights
        
        # Check weighted components calculation
        weighted_components = result["weighted_components"]
        
        # Load balance: 80 * 0.4 = 32
        assert weighted_components["load_balance"]["weighted_component"] == pytest.approx(32.0, rel=1e-2)
        
        # Classroom changes: 70 * 0.2 = 14
        assert weighted_components["classroom_changes"]["weighted_component"] == pytest.approx(14.0, rel=1e-2)
        
        # Time efficiency: 90 * 0.2 = 18
        assert weighted_components["time_efficiency"]["weighted_component"] == pytest.approx(18.0, rel=1e-2)
        
        # Session minimization: 85 * 0.1 = 8.5
        assert weighted_components["session_minimization"]["weighted_component"] == pytest.approx(8.5, rel=1e-2)
        
        # Rule compliance: 95 * 0.1 = 9.5
        assert weighted_components["rule_compliance"]["weighted_component"] == pytest.approx(9.5, rel=1e-2)
        
        # Total: 32 + 14 + 18 + 8.5 + 9.5 = 82
        assert result["total_weighted_score"] == pytest.approx(82.0, rel=1e-2)
    
    def test_calculate_weighted_score_normalized_to_100(self, weights_service):
        """Test that final score is normalized to 0-100 range"""
        objective_scores = {
            "load_balance": 100.0,
            "classroom_changes": 100.0,
            "time_efficiency": 100.0,
            "session_minimization": 100.0,
            "rule_compliance": 100.0
        }
        
        result = weights_service.calculate_weighted_score(objective_scores)
        
        # All scores are 100, so weighted sum should be 100
        assert result["total_weighted_score"] == pytest.approx(100.0, rel=1e-2)
        assert result["normalized_final_score"] == 100.0
    
    def test_calculate_weighted_score_zero_scores(self, weights_service):
        """Test weighted score calculation with zero scores"""
        objective_scores = {
            "load_balance": 0.0,
            "classroom_changes": 0.0,
            "time_efficiency": 0.0,
            "session_minimization": 0.0,
            "rule_compliance": 0.0
        }
        
        result = weights_service.calculate_weighted_score(objective_scores)
        
        assert result["success"] == True
        assert result["total_weighted_score"] == 0.0
        assert result["normalized_final_score"] == 0.0
    
    def test_calculate_weighted_score_missing_objectives(self, weights_service):
        """Test weighted score calculation with missing objectives"""
        objective_scores = {
            "load_balance": 80.0,
            "classroom_changes": 70.0,
            # Missing other objectives
        }
        
        result = weights_service.calculate_weighted_score(objective_scores)
        
        assert result["success"] == True
        
        # Should only calculate for provided objectives
        weighted_components = result["weighted_components"]
        assert "load_balance" in weighted_components
        assert "classroom_changes" in weighted_components
        assert "time_efficiency" not in weighted_components
        assert "session_minimization" not in weighted_components
        assert "rule_compliance" not in weighted_components
    
    def test_validate_objective_scores_valid(self, weights_service):
        """Test objective scores validation with valid scores"""
        scores = {
            "load_balance": 80.0,
            "classroom_changes": 70.0,
            "time_efficiency": 90.0,
            "session_minimization": 85.0,
            "rule_compliance": 95.0
        }
        
        result = weights_service._validate_objective_scores(scores)
        
        assert result["valid"] == True
        assert len(result["errors"]) == 0
    
    def test_validate_objective_scores_invalid_range(self, weights_service):
        """Test objective scores validation with invalid range"""
        scores = {
            "load_balance": 150.0,  # > 100
            "classroom_changes": -10.0,  # < 0
            "time_efficiency": 90.0,
            "session_minimization": 85.0,
            "rule_compliance": 95.0
        }
        
        result = weights_service._validate_objective_scores(scores)
        
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        assert any("must be between 0 and 100" in error for error in result["errors"])
    
    def test_validate_objective_scores_invalid_type(self, weights_service):
        """Test objective scores validation with invalid types"""
        scores = {
            "load_balance": "invalid",  # Not a number
            "classroom_changes": 70.0,
            "time_efficiency": 90.0,
            "session_minimization": 85.0,
            "rule_compliance": 95.0
        }
        
        result = weights_service._validate_objective_scores(scores)
        
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        assert any("must be a number" in error for error in result["errors"])
    
    def test_normalize_objective_score_different_types(self, weights_service):
        """Test objective score normalization for different types"""
        # Load balance (higher is better)
        normalized = weights_service._normalize_objective_score("load_balance", 80.0)
        assert normalized == 80.0
        
        # Classroom changes (lower is better, inverted)
        normalized = weights_service._normalize_objective_score("classroom_changes", 20.0)  # 20 changes
        assert normalized == 80.0  # Should be inverted to 80
        
        # Time efficiency (higher is better)
        normalized = weights_service._normalize_objective_score("time_efficiency", 90.0)
        assert normalized == 90.0
        
        # Session minimization (lower is better, inverted)
        normalized = weights_service._normalize_objective_score("session_minimization", 10.0)  # 10 sessions
        assert normalized == 90.0  # Should be inverted to 90
        
        # Rule compliance (higher is better)
        normalized = weights_service._normalize_objective_score("rule_compliance", 95.0)
        assert normalized == 95.0
    
    def test_weights_normalization(self, weights_service):
        """Test weights normalization"""
        # Test normalized weights
        normalized_weights = {
            "load_balance": 0.3,
            "classroom_changes": 0.2,
            "time_efficiency": 0.2,
            "session_minimization": 0.15,
            "rule_compliance": 0.15
        }
        
        assert weights_service._are_weights_normalized(normalized_weights) == True
        
        # Test non-normalized weights
        non_normalized_weights = {
            "load_balance": 0.3,
            "classroom_changes": 0.2,
            "time_efficiency": 0.2,
            "session_minimization": 0.15,
            "rule_compliance": 0.2  # Total = 1.05
        }
        
        assert weights_service._are_weights_normalized(non_normalized_weights) == False
    
    def test_default_weights_sum_to_one(self, weights_service):
        """Test that default weights sum to 1.0"""
        default_weights = weights_service.default_weights
        total_weight = sum(default_weights.values())
        
        assert abs(total_weight - 1.0) < 0.01  # Allow small floating point errors
    
    def test_weighted_score_with_progress_tracking(self, weights_service):
        """Test weighted score calculation with progress tracking"""
        objective_scores = {
            "load_balance": 80.0,
            "classroom_changes": 70.0,
            "time_efficiency": 90.0,
            "session_minimization": 85.0,
            "rule_compliance": 95.0
        }
        
        result = weights_service.calculate_weighted_score(objective_scores)
        
        # Check that all required fields are present
        required_fields = [
            "success",
            "total_weighted_score",
            "weighted_components",
            "weights_used",
            "objective_scores",
            "project_specification_formula",
            "normalized_final_score"
        ]
        
        for field in required_fields:
            assert field in result
        
        # Check weighted components structure
        weighted_components = result["weighted_components"]
        for objective, component in weighted_components.items():
            required_component_fields = [
                "raw_score",
                "normalized_score",
                "weight",
                "weighted_component",
                "description"
            ]
            
            for field in required_component_fields:
                assert field in component
    
    def test_error_handling_invalid_input(self, weights_service):
        """Test error handling with invalid input"""
        # Test with None input
        result = weights_service.calculate_weighted_score(None)
        assert result["success"] == False
        assert "message" in result
        
        # Test with empty input
        result = weights_service.calculate_weighted_score({})
        assert result["success"] == False
        assert "message" in result
        
        # Test with invalid weights
        objective_scores = {
            "load_balance": 80.0,
            "classroom_changes": 70.0
        }
        
        invalid_weights = {
            "load_balance": "invalid",  # Not a number
            "classroom_changes": 0.5
        }
        
        result = weights_service.calculate_weighted_score(objective_scores, invalid_weights)
        # Should still work but use default weights for invalid entries
        assert result["success"] == True


if __name__ == "__main__":
    pytest.main([__file__])
