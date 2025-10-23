"""
Unit tests for algorithm services.
"""
import pytest
from app.services.algorithm import AlgorithmService
from app.algorithms.factory import AlgorithmFactory
from app.models.algorithm import AlgorithmType


class TestAlgorithmService:
    """Test AlgorithmService class."""
    
    def test_list_algorithms(self):
        """Test listing available algorithms."""
        service = AlgorithmService()
        algorithms = service.list_algorithms()
        
        assert isinstance(algorithms, list)
        assert len(algorithms) > 0
        
        # Check algorithm structure
        for algorithm in algorithms:
            assert "type" in algorithm
            assert "name" in algorithm
            assert "description" in algorithm
            assert "best_for" in algorithm
    
    def test_run_algorithm_greedy(self):
        """Test running greedy algorithm."""
        service = AlgorithmService()
        
        # Test with empty data
        result = service.run_algorithm("greedy", {})
        
        assert result is not None
        assert "schedule" in result
        assert "metrics" in result
        assert "execution_time" in result
    
    def test_run_algorithm_genetic(self):
        """Test running genetic algorithm."""
        service = AlgorithmService()
        
        # Test with empty data
        result = service.run_algorithm("genetic_algorithm", {})
        
        assert result is not None
        assert "schedule" in result
        assert "metrics" in result
        assert "execution_time" in result
    
    def test_run_algorithm_simplex(self):
        """Test running simplex algorithm."""
        service = AlgorithmService()
        
        # Test with empty data
        result = service.run_algorithm("simplex", {})
        
        assert result is not None
        assert "schedule" in result
        assert "metrics" in result
        assert "execution_time" in result
    
    def test_run_invalid_algorithm(self):
        """Test running invalid algorithm."""
        service = AlgorithmService()
        
        with pytest.raises(ValueError):
            service.run_algorithm("invalid_algorithm", {})


class TestAlgorithmFactory:
    """Test AlgorithmFactory class."""
    
    def test_get_algorithm_types(self):
        """Test getting available algorithm types."""
        from app.algorithms.factory import get_algorithm_types
        
        algorithm_types = get_algorithm_types()
        
        assert isinstance(algorithm_types, list)
        assert len(algorithm_types) > 0
        
        # Check if expected algorithms are present
        expected_algorithms = ["greedy", "genetic_algorithm", "simplex", "tabu_search"]
        for expected in expected_algorithms:
            assert any(algo["type"] == expected for algo in algorithm_types)
    
    def test_create_algorithm(self):
        """Test creating algorithm instances."""
        factory = AlgorithmFactory()
        
        # Test creating greedy algorithm
        greedy_algo = factory.create_algorithm(AlgorithmType.GREEDY)
        assert greedy_algo is not None
        
        # Test creating genetic algorithm
        genetic_algo = factory.create_algorithm(AlgorithmType.GENETIC_ALGORITHM)
        assert genetic_algo is not None
        
        # Test creating simplex algorithm
        simplex_algo = factory.create_algorithm(AlgorithmType.SIMPLEX)
        assert simplex_algo is not None
    
    def test_create_invalid_algorithm(self):
        """Test creating invalid algorithm."""
        factory = AlgorithmFactory()
        
        with pytest.raises(ValueError):
            factory.create_algorithm("invalid_type")


class TestAlgorithmExecution:
    """Test algorithm execution scenarios."""
    
    def test_algorithm_with_empty_data(self):
        """Test algorithm execution with empty data."""
        service = AlgorithmService()
        
        # Test all algorithms with empty data
        algorithms = ["greedy", "genetic_algorithm", "simplex", "tabu_search"]
        
        for algorithm_type in algorithms:
            result = service.run_algorithm(algorithm_type, {})
            
            assert result is not None
            assert isinstance(result["schedule"], list)
            assert isinstance(result["metrics"], dict)
            assert isinstance(result["execution_time"], (int, float))
    
    def test_algorithm_with_parameters(self):
        """Test algorithm execution with parameters."""
        service = AlgorithmService()
        
        parameters = {
            "max_iterations": 100,
            "timeout": 30,
            "population_size": 50
        }
        
        result = service.run_algorithm("genetic_algorithm", parameters)
        
        assert result is not None
        assert result["execution_time"] < 30.0  # Should respect timeout
    
    def test_algorithm_performance(self):
        """Test algorithm performance."""
        service = AlgorithmService()
        
        import time
        
        start_time = time.time()
        result = service.run_algorithm("greedy", {})
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result is not None
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert result["execution_time"] < 5.0


class TestAlgorithmValidation:
    """Test algorithm input validation."""
    
    def test_validate_algorithm_type(self):
        """Test algorithm type validation."""
        service = AlgorithmService()
        
        # Valid algorithm types
        valid_types = ["greedy", "genetic_algorithm", "simplex", "tabu_search"]
        for algo_type in valid_types:
            # Should not raise exception
            result = service.run_algorithm(algo_type, {})
            assert result is not None
        
        # Invalid algorithm type
        with pytest.raises(ValueError):
            service.run_algorithm("invalid", {})
    
    def test_validate_parameters(self):
        """Test parameter validation."""
        service = AlgorithmService()
        
        # Valid parameters
        valid_params = {
            "max_iterations": 100,
            "timeout": 30
        }
        
        result = service.run_algorithm("greedy", valid_params)
        assert result is not None
        
        # Invalid parameters (negative values)
        invalid_params = {
            "max_iterations": -1,
            "timeout": -5
        }
        
        # Should handle gracefully
        result = service.run_algorithm("greedy", invalid_params)
        assert result is not None
