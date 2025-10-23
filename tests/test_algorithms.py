"""
Tests for optimization algorithms
"""

import pytest
from app.algorithms.ant_colony import AntColony
from app.algorithms.lexicographic import LexicographicAlgorithm
from app.algorithms.hybrid_cp_sat_nsga import HybridCPSATNSGAAlgorithm
from app.algorithms.real_simplex import RealSimplexAlgorithm
from app.algorithms.optimized_genetic_algorithm import OptimizedGeneticAlgorithm
from app.algorithms.factory import AlgorithmFactory
from app.models.algorithm import AlgorithmType


class TestLexicographicAlgorithm:
    """Test cases for Lexicographic algorithm."""
    
    def test_initialization(self):
        """Test algorithm initialization."""
        params = {
            "objective_order": ["load_balance", "classroom_changes"],
            "max_iterations": 100
        }
        algo = LexicographicAlgorithm(params)
        
        assert algo.name == "Lexicographic"
        assert algo.objective_order == ["load_balance", "classroom_changes"]
        assert algo.max_iterations == 100
    
    def test_initialization_default_params(self):
        """Test algorithm initialization with default parameters."""
        algo = LexicographicAlgorithm()
        
        assert algo.name == "Lexicographic"
        assert len(algo.objective_order) == 4
        assert algo.max_iterations == 1000
    
    def test_optimize(self, test_data):
        """Test algorithm optimization."""
        algo = LexicographicAlgorithm({"max_iterations": 10})
        algo.initialize(test_data)
        
        result = algo.optimize(test_data)
        
        assert "solution" in result
        assert "fitness_scores" in result
        assert "execution_time" in result
        assert "iterations" in result
        assert result["algorithm"] == "Lexicographic"
    
    def test_calculate_load_balance_score(self, test_data):
        """Test load balance score calculation."""
        algo = LexicographicAlgorithm()
        algo.initialize(test_data)
        
        solution = [
            {"project_id": 1, "instructors": [1, 2]},
            {"project_id": 2, "instructors": [1]}
        ]
        
        score = algo._calculate_load_balance_score(solution)
        assert isinstance(score, float)
        assert score >= 0
    
    def test_calculate_classroom_changes_score(self, test_data):
        """Test classroom changes score calculation."""
        algo = LexicographicAlgorithm()
        algo.initialize(test_data)
        
        solution = [
            {"project_id": 1, "classroom_id": 1, "instructors": [1]},
            {"project_id": 2, "classroom_id": 2, "instructors": [1]}
        ]
        
        score = algo._calculate_classroom_changes_score(solution)
        assert isinstance(score, float)
        assert score >= 0


class TestHybridCPSATNSGAAlgorithm:
    """Test cases for Hybrid CP-SAT + NSGA-II algorithm."""
    
    def test_initialization(self):
        """Test algorithm initialization."""
        params = {
            "cp_sat_timeout": 30,
            "use_real_ortools": False,
            "population_size": 50,
            "generations": 25
        }
        algo = HybridCPSATNSGAAlgorithm(params)
        
        assert algo.name == "Hybrid CP-SAT + NSGA-II"
        assert algo.cp_sat_timeout == 30
        assert algo.use_real_ortools == False
        assert algo.population_size == 50
        assert algo.generations == 25
    
    def test_initialization_default_params(self):
        """Test algorithm initialization with default parameters."""
        algo = HybridCPSATNSGAAlgorithm()
        
        assert algo.name == "Hybrid CP-SAT + NSGA-II"
        assert algo.cp_sat_timeout == 30
        assert algo.use_real_ortools == False
        assert algo.population_size == 100
        assert algo.generations == 50
    
    def test_optimize(self, test_data):
        """Test algorithm optimization."""
        algo = HybridCPSATNSGAAlgorithm({
            "population_size": 10,
            "generations": 5,
            "use_real_ortools": False
        })
        algo.initialize(test_data)
        
        result = algo.optimize(test_data)
        
        assert "solution" in result
        assert "fitness_scores" in result
        assert "execution_time" in result
        assert "generations" in result
        assert "population_size" in result
        assert result["algorithm"] == "Hybrid CP-SAT + NSGA-II"
    
    def test_simulate_cp_sat(self, test_data):
        """Test CP-SAT simulation."""
        algo = HybridCPSATNSGAAlgorithm()
        algo.initialize(test_data)
        
        solutions = algo._simulate_cp_sat()
        
        assert isinstance(solutions, list)
        for solution in solutions:
            assert "assignment" in solution
            assert "method" in solution
            assert "status" in solution
    
    def test_generate_random_solution(self, test_data):
        """Test random solution generation."""
        algo = HybridCPSATNSGAAlgorithm()
        algo.initialize(test_data)
        
        solution = algo._generate_random_solution()
        
        assert "assignment" in solution
        assert "method" in solution
        assert solution["method"] == "random"
        assert isinstance(solution["assignment"], list)


class TestRealSimplexAlgorithm:
    """Test cases for Real Simplex algorithm."""
    
    def test_initialization(self):
        """Test algorithm initialization."""
        params = {
            "max_iterations": 100,
            "tolerance": 1e-6,
            "timeout": 30
        }
        algo = RealSimplexAlgorithm(params)
        
        assert algo.name == "Real Simplex Algorithm (Linear Programming)"
        assert algo.max_iterations == 100
        assert algo.tolerance == 1e-6
        assert algo.timeout == 30


class TestOptimizedGeneticAlgorithm:
    """Test cases for Optimized Genetic Algorithm."""
    
    def test_initialization(self):
        """Test algorithm initialization."""
        params = {
            "population_size": 50,
            "generations": 100,
            "mutation_rate": 0.1,
            "crossover_rate": 0.8,
            "elite_size": 5
        }
        algo = OptimizedGeneticAlgorithm(params)
        
        assert algo.name == "Optimized Genetic Algorithm"
        assert algo.population_size == 50
        assert algo.generations == 100
        assert algo.mutation_rate == 0.1
        assert algo.crossover_rate == 0.8
        assert algo.elite_size == 5
    
    def test_initialization_default_params(self):
        """Test algorithm initialization with default parameters."""
        algo = OptimizedGeneticAlgorithm()
        
        assert algo.name == "Optimized Genetic Algorithm"
        assert algo.population_size == 100
        assert algo.generations == 200
        assert algo.mutation_rate == 0.1
        assert algo.crossover_rate == 0.8
        assert algo.elite_size == 10
    
    def test_optimization(self, test_data):
        """Test algorithm optimization."""
        algo = OptimizedGeneticAlgorithm({
            "population_size": 20,
            "generations": 10,
            "mutation_rate": 0.1,
            "crossover_rate": 0.8
        })
        
        result = algo.optimize(test_data)
        
        assert result["algorithm"] == "Optimized Genetic Algorithm"
        assert result["status"] == "completed"
        assert "schedule" in result
        assert "metrics" in result
        assert "execution_time" in result
        assert "generations" in result
        assert "final_fitness" in result
    
    def test_fitness_evaluation(self, test_data):
        """Test fitness evaluation."""
        algo = OptimizedGeneticAlgorithm()
        algo.initialize(test_data)
        
        # Create a test individual
        individual = [
            {
                "project_id": 1,
                "classroom_id": 1,
                "timeslot_id": 1,
                "instructors": [1, 2],
                "is_makeup": False
            }
        ]
        
        fitness = algo.evaluate_fitness(individual)
        assert isinstance(fitness, float)
        assert 0 <= fitness <= 100
    
    def test_load_balance_score(self, test_data):
        """Test load balance score calculation."""
        algo = OptimizedGeneticAlgorithm()
        algo.initialize(test_data)
        
        # Test individual with balanced load
        individual = [
            {
                "project_id": 1,
                "classroom_id": 1,
                "timeslot_id": 1,
                "instructors": [1, 2],
                "is_makeup": False
            },
            {
                "project_id": 2,
                "classroom_id": 2,
                "timeslot_id": 2,
                "instructors": [1, 3],
                "is_makeup": False
            }
        ]
        
        score = algo._calculate_load_balance_score(individual)
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_classroom_change_score(self, test_data):
        """Test classroom change score calculation."""
        algo = OptimizedGeneticAlgorithm()
        algo.initialize(test_data)
        
        # Test individual with no classroom changes
        individual = [
            {
                "project_id": 1,
                "classroom_id": 1,
                "timeslot_id": 1,
                "instructors": [1, 2],
                "is_makeup": False
            },
            {
                "project_id": 2,
                "classroom_id": 1,
                "timeslot_id": 2,
                "instructors": [1, 3],
                "is_makeup": False
            }
        ]
        
        score = algo._calculate_classroom_change_score(individual)
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_rule_compliance_score(self, test_data):
        """Test rule compliance score calculation."""
        algo = OptimizedGeneticAlgorithm()
        algo.initialize(test_data)
        
        # Test individual with proper instructor assignments
        individual = [
            {
                "project_id": 1,
                "classroom_id": 1,
                "timeslot_id": 1,
                "instructors": [1, 2],  # Bitirme project with 2 instructors
                "is_makeup": False
            },
            {
                "project_id": 2,
                "classroom_id": 2,
                "timeslot_id": 2,
                "instructors": [3],  # Ara project with 1 instructor
                "is_makeup": False
            }
        ]
        
        score = algo._calculate_rule_compliance_score(individual)
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_comprehensive_metrics(self, test_data):
        """Test comprehensive metrics calculation."""
        algo = OptimizedGeneticAlgorithm()
        algo.initialize(test_data)
        
        individual = [
            {
                "project_id": 1,
                "classroom_id": 1,
                "timeslot_id": 1,
                "instructors": [1, 2],
                "is_makeup": False
            }
        ]
        
        metrics = algo._calculate_comprehensive_metrics(individual)
        
        assert "load_balance_score" in metrics
        assert "classroom_change_score" in metrics
        assert "time_efficiency_score" in metrics
        assert "slot_minimization_score" in metrics
        assert "rule_compliance_score" in metrics
        assert "overall_score" in metrics
        assert "weights" in metrics
        
        # Check that all scores are between 0 and 100
        for key in ["load_balance_score", "classroom_change_score", "time_efficiency_score", 
                   "slot_minimization_score", "rule_compliance_score", "overall_score"]:
            assert 0 <= metrics[key] <= 100
    
    def test_initialization_default_params(self):
        """Test algorithm initialization with default parameters."""
        algo = RealSimplexAlgorithm()
        
        assert algo.name == "Real Simplex Algorithm (Linear Programming)"
        assert algo.max_iterations == 1000
        assert algo.tolerance == 1e-8
        assert algo.timeout == 30
    
    def test_optimize(self, test_data):
        """Test algorithm optimization."""
        algo = OptimizedSimplexAlgorithm({"max_iterations": 10})
        algo.initialize(test_data)
        
        result = algo.optimize(test_data)
        
        assert "schedule" in result
        assert "solution" in result
        assert "metrics" in result
        assert "execution_time" in result
        assert "iterations" in result
        assert result["algorithm"] == "Optimized Simplex"
    
    def test_calculate_load_balance_score(self, test_data):
        """Test load balance score calculation."""
        algo = RealSimplexAlgorithm()
        algo.initialize(test_data)
        
        solution = [
            {"project_id": 1, "instructors": [1, 2]},
            {"project_id": 2, "instructors": [1, 3]},
            {"project_id": 3, "instructors": [2, 3]}
        ]
        
        score = algo._calculate_load_balance_score(solution)
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_calculate_classroom_change_score(self, test_data):
        """Test classroom change score calculation."""
        algo = RealSimplexAlgorithm()
        algo.initialize(test_data)
        
        solution = [
            {"project_id": 1, "classroom_id": 1, "instructors": [1]},
            {"project_id": 2, "classroom_id": 1, "instructors": [1]},
            {"project_id": 3, "classroom_id": 2, "instructors": [2]}
        ]
        
        score = algo._calculate_classroom_change_score(solution)
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_assign_instructors_to_project_bitirme(self, test_data):
        """Test instructor assignment for bitirme projects."""
        algo = RealSimplexAlgorithm()
        algo.initialize(test_data)
        
        project = {"id": 1, "type": "bitirme"}
        instructors = algo._assign_instructors_to_project(project)
        
        # Bitirme projects need at least 2 instructors
        assert len(instructors) >= 2
        assert all(isinstance(inst_id, int) for inst_id in instructors)
    
    def test_assign_instructors_to_project_ara(self, test_data):
        """Test instructor assignment for ara projects."""
        algo = RealSimplexAlgorithm()
        algo.initialize(test_data)
        
        project = {"id": 1, "type": "ara"}
        instructors = algo._assign_instructors_to_project(project)
        
        # Ara projects need at least 1 instructor
        assert len(instructors) >= 1
        assert all(isinstance(inst_id, int) for inst_id in instructors)
    
    def test_validate_solution(self, test_data):
        """Test solution validation."""
        algo = RealSimplexAlgorithm()
        algo.initialize(test_data)
        
        # Valid solution
        valid_solution = [
            {"project_id": 1, "classroom_id": 1, "timeslot_id": 1, "instructors": [1, 2]},
            {"project_id": 2, "classroom_id": 2, "timeslot_id": 2, "instructors": [3]}
        ]
        
        validation = algo._validate_solution(valid_solution)
        assert "is_feasible" in validation
        assert "violations" in validation
        assert "violation_count" in validation
    
    def test_calculate_comprehensive_metrics(self, test_data):
        """Test comprehensive metrics calculation."""
        algo = RealSimplexAlgorithm()
        algo.initialize(test_data)
        
        solution = [
            {"project_id": 1, "classroom_id": 1, "timeslot_id": 1, "instructors": [1, 2]},
            {"project_id": 2, "classroom_id": 2, "timeslot_id": 2, "instructors": [3]}
        ]
        
        metrics = algo._calculate_comprehensive_metrics(solution)
        
        assert "load_balance_score" in metrics
        assert "classroom_change_score" in metrics
        assert "time_efficiency_score" in metrics
        assert "slot_minimization_score" in metrics
        assert "rule_compliance_score" in metrics
        assert "overall_score" in metrics
        assert "weights" in metrics
        
        # All scores should be between 0 and 100
        for key in ["load_balance_score", "classroom_change_score", "time_efficiency_score", 
                   "slot_minimization_score", "rule_compliance_score", "overall_score"]:
            assert 0 <= metrics[key] <= 100


class TestAlgorithmFactory:
    """Test cases for Algorithm factory."""
    
    def test_create_lexicographic(self):
        """Test creating Lexicographic algorithm."""
        algo = AlgorithmFactory.create(AlgorithmType.LEXICOGRAPHIC)
        assert isinstance(algo, LexicographicAlgorithm)
    
    def test_create_hybrid(self):
        """Test creating Hybrid algorithm."""
        algo = AlgorithmFactory.create(AlgorithmType.HYBRID_CP_SAT_NSGA)
        assert isinstance(algo, HybridCPSATNSGAAlgorithm)
    
    def test_create_simplex(self):
        """Test creating Optimized Simplex algorithm."""
        algo = AlgorithmFactory.create(AlgorithmType.SIMPLEX)
        assert isinstance(algo, OptimizedSimplexAlgorithm)
    
    def test_create_with_params(self):
        """Test creating algorithm with parameters."""
        params = {"max_iterations": 50}
        algo = AlgorithmFactory.create(AlgorithmType.LEXICOGRAPHIC, params)
        assert algo.max_iterations == 50
    
    def test_create_invalid_type(self):
        """Test creating invalid algorithm type."""
        with pytest.raises(ValueError):
            AlgorithmFactory.create("invalid_type")


def test_ant_colony_gap_penalty():
    """Test Ant Colony gap penalty mechanism."""
    # Test verilerini hazırla
    data = {
        "instructors": [
            {"id": 1, "type": "professor"},
            {"id": 2, "type": "research_assistant"}
        ],
        "projects": [
            {"id": 1, "responsible_id": 1, "type": "bitirme"},
            {"id": 2, "responsible_id": 2, "type": "ara"}
        ],
        "classrooms": [
            {"id": 1, "capacity": 30},
            {"id": 2, "capacity": 25}
        ],
        "timeslots": [
            {"id": 1, "start_time": "09:00", "end_time": "09:30", "is_morning": True},
            {"id": 2, "start_time": "09:30", "end_time": "10:00", "is_morning": True},
            {"id": 3, "start_time": "10:00", "end_time": "10:30", "is_morning": True},
            {"id": 4, "start_time": "13:00", "end_time": "13:30", "is_morning": False},
            {"id": 5, "start_time": "13:30", "end_time": "14:00", "is_morning": False},
            {"id": 6, "start_time": "14:00", "end_time": "14:30", "is_morning": False}
        ]
    }

    # Ant Colony algoritmasını başlat
    ant_colony = AntColony()
    ant_colony.initialize(data)

    # Test 1: Geçerli çözüm (boşluk yok)
    valid_solution = [
        {
            "project_id": 1,
            "classroom_id": 1,
            "timeslot_id": 1,  # 09:00-09:30
            "instructors": [1]
        },
        {
            "project_id": 2,
            "classroom_id": 2,
            "timeslot_id": 2,  # 09:30-10:00
            "instructors": [2]
        }
    ]

    gap_penalty_valid = ant_colony._calculate_gap_penalty(valid_solution)
    assert gap_penalty_valid == 0.0, "Geçerli çözümde boşluk cezası olmamalı"

    # Test 2: Geçersiz çözüm (boşluk var - 09:00-09:30 ve 10:00-10:30 dolu, 09:30-10:00 boş)
    invalid_solution = [
        {
            "project_id": 1,
            "classroom_id": 1,
            "timeslot_id": 1,  # 09:00-09:30
            "instructors": [1]
        },
        {
            "project_id": 2,
            "classroom_id": 2,
            "timeslot_id": 3,  # 10:00-10:30
            "instructors": [2]
        }
    ]

    gap_penalty_invalid = ant_colony._calculate_gap_penalty(invalid_solution)
    assert gap_penalty_invalid == -9999.0, "Geçersiz çözümde -9999 ceza olmalı"

    # Test 3: Öğleden sonra slotları için test
    afternoon_valid = [
        {
            "project_id": 1,
            "classroom_id": 1,
            "timeslot_id": 4,  # 13:00-13:30
            "instructors": [1]
        },
        {
            "project_id": 2,
            "classroom_id": 2,
            "timeslot_id": 5,  # 13:30-14:00
            "instructors": [2]
        }
    ]

    gap_penalty_afternoon = ant_colony._calculate_gap_penalty(afternoon_valid)
    assert gap_penalty_afternoon == 0.0, "Geçerli öğleden sonra çözümde ceza olmamalı"