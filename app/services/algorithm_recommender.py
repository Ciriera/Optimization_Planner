"""
Algorithm recommendation service
Provides intelligent algorithm recommendations based on problem characteristics
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProblemComplexity(Enum):
    """Problem complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AlgorithmRecommendation:
    """Algorithm recommendation with reasoning"""
    
    def __init__(self, algorithm_name: str, confidence: float, reasoning: str, 
                 expected_performance: Dict[str, Any]):
        self.algorithm_name = algorithm_name
        self.confidence = confidence  # 0.0 to 1.0
        self.reasoning = reasoning
        self.expected_performance = expected_performance


class AlgorithmRecommender:
    """Service for recommending optimal algorithms based on problem characteristics"""
    
    def __init__(self):
        # Algorithm characteristics mapping
        self.algorithm_characteristics = {
            "simplex": {
                "best_for": ["small_problems", "linear_constraints", "quick_solution"],
                "complexity": ProblemComplexity.LOW,
                "strengths": ["Fast", "Deterministic", "Guaranteed optimal"],
                "weaknesses": ["Limited scalability", "Linear constraints only"],
                "performance_indicators": {
                    "speed": 0.9,
                    "accuracy": 0.95,
                    "scalability": 0.3
                }
            },
            "simulated_annealing": {
                "best_for": ["classroom_changes_minimization", "global_optimization"],
                "complexity": ProblemComplexity.MEDIUM,
                "strengths": ["Global optimization", "Handles complex constraints"],
                "weaknesses": ["Slow convergence", "Parameter sensitive"],
                "performance_indicators": {
                    "speed": 0.6,
                    "accuracy": 0.8,
                    "scalability": 0.7
                }
            },
            "tabu_search": {
                "best_for": ["classroom_conflicts", "local_optimization"],
                "complexity": ProblemComplexity.MEDIUM,
                "strengths": ["Avoids local optima", "Good for scheduling"],
                "weaknesses": ["Memory intensive", "Complex parameter tuning"],
                "performance_indicators": {
                    "speed": 0.7,
                    "accuracy": 0.85,
                    "scalability": 0.6
                }
            },
            "genetic_algorithm": {
                "best_for": ["diversity_required", "multi_objective"],
                "complexity": ProblemComplexity.HIGH,
                "strengths": ["Population diversity", "Multi-objective capable"],
                "weaknesses": ["Slow", "No convergence guarantee"],
                "performance_indicators": {
                    "speed": 0.5,
                    "accuracy": 0.75,
                    "scalability": 0.8
                }
            },
            "cp_sat": {
                "best_for": ["strict_constraints", "rule_compliance"],
                "complexity": ProblemComplexity.MEDIUM,
                "strengths": ["Guaranteed feasibility", "Handles complex constraints"],
                "weaknesses": ["Limited optimization", "Scalability issues"],
                "performance_indicators": {
                    "speed": 0.6,
                    "accuracy": 1.0,  # Always feasible
                    "scalability": 0.5
                }
            },
            "nsga_ii": {
                "best_for": ["multi_objective", "pareto_optimality"],
                "complexity": ProblemComplexity.HIGH,
                "strengths": ["Multiple objectives", "Pareto optimal solutions"],
                "weaknesses": ["Complex", "Slow convergence"],
                "performance_indicators": {
                    "speed": 0.4,
                    "accuracy": 0.9,
                    "scalability": 0.7
                }
            },
            "hybrid_cp_sat_nsga": {
                "best_for": ["balanced_approach", "best_of_both_worlds"],
                "complexity": ProblemComplexity.VERY_HIGH,
                "strengths": ["Feasibility + Optimization", "High quality solutions"],
                "weaknesses": ["Complex", "Slow"],
                "performance_indicators": {
                    "speed": 0.3,
                    "accuracy": 0.95,
                    "scalability": 0.6
                }
            },
            "lexicographic": {
                "best_for": ["priority_based", "critical_constraints"],
                "complexity": ProblemComplexity.MEDIUM,
                "strengths": ["Priority handling", "Guaranteed constraint satisfaction"],
                "weaknesses": ["Sequential optimization", "May miss global optimum"],
                "performance_indicators": {
                    "speed": 0.7,
                    "accuracy": 0.9,
                    "scalability": 0.7
                }
            },
            "deep_search": {
                "best_for": ["local_refinement", "solution_improvement"],
                "complexity": ProblemComplexity.MEDIUM,
                "strengths": ["Deep local search", "Solution improvement"],
                "weaknesses": ["Local optima", "Requires good initial solution"],
                "performance_indicators": {
                    "speed": 0.6,
                    "accuracy": 0.8,
                    "scalability": 0.6
                }
            },
            "greedy": {
                "best_for": ["quick_solution", "low_complexity"],
                "complexity": ProblemComplexity.LOW,
                "strengths": ["Very fast", "Simple implementation"],
                "weaknesses": ["Poor quality", "No global view"],
                "performance_indicators": {
                    "speed": 1.0,
                    "accuracy": 0.5,
                    "scalability": 0.9
                }
            }
        }
    
    def recommend_algorithm(self, problem_context: Dict[str, Any]) -> List[AlgorithmRecommendation]:
        """
        Problem context'e göre algoritma önerisi yapar.
        
        Args:
            problem_context: Problem karakteristikleri
            
        Returns:
            Algoritma önerileri listesi (confidence'e göre sıralı)
        """
        # Problem karakteristiklerini analiz et
        analysis = self._analyze_problem_context(problem_context)
        
        # Her algoritma için uygunluk skoru hesapla
        recommendations = []
        
        for algo_name, characteristics in self.algorithm_characteristics.items():
            score = self._calculate_algorithm_score(algo_name, characteristics, analysis)
            
            if score > 0.3:  # Minimum threshold
                recommendation = AlgorithmRecommendation(
                    algorithm_name=algo_name,
                    confidence=score,
                    reasoning=self._generate_reasoning(algo_name, characteristics, analysis),
                    expected_performance=characteristics["performance_indicators"]
                )
                recommendations.append(recommendation)
        
        # Confidence'e göre sırala
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        return recommendations
    
    def _analyze_problem_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Problem context'ini analiz eder"""
        analysis = {
            "problem_size": self._assess_problem_size(context),
            "constraint_complexity": self._assess_constraint_complexity(context),
            "time_requirement": context.get("time_requirement", "medium"),
            "quality_requirement": context.get("quality_requirement", "high"),
            "multi_objective": context.get("multi_objective", True),
            "priority_focus": context.get("priority_focus", None)
        }
        
        return analysis
    
    def _assess_problem_size(self, context: Dict[str, Any]) -> ProblemComplexity:
        """Problem boyutunu değerlendirir"""
        project_count = context.get("project_count", 0)
        instructor_count = context.get("instructor_count", 0)
        classroom_count = context.get("classroom_count", 0)
        
        total_size = project_count + instructor_count + classroom_count
        
        if total_size < 20:
            return ProblemComplexity.LOW
        elif total_size < 50:
            return ProblemComplexity.MEDIUM
        elif total_size < 100:
            return ProblemComplexity.HIGH
        else:
            return ProblemComplexity.VERY_HIGH
    
    def _assess_constraint_complexity(self, context: Dict[str, Any]) -> str:
        """Constraint karmaşıklığını değerlendirir"""
        has_makeup_separation = context.get("has_makeup_separation", False)
        has_strict_rules = context.get("has_strict_rules", True)
        has_time_blocks = context.get("has_time_blocks", True)
        
        if has_makeup_separation and has_strict_rules and has_time_blocks:
            return "very_high"
        elif has_strict_rules and has_time_blocks:
            return "high"
        elif has_strict_rules or has_time_blocks:
            return "medium"
        else:
            return "low"
    
    def _calculate_algorithm_score(self, algo_name: str, characteristics: Dict[str, Any], 
                                 analysis: Dict[str, Any]) -> float:
        """Algoritma için uygunluk skoru hesaplar"""
        score = 0.0
        
        # Problem boyutu uygunluğu
        algo_complexity = characteristics["complexity"]
        problem_size = analysis["problem_size"]
        
        if algo_complexity == problem_size:
            score += 0.3
        elif self._complexity_compatibility(algo_complexity, problem_size):
            score += 0.2
        else:
            score += 0.1
        
        # Zaman gereksinimi
        time_req = analysis["time_requirement"]
        speed_score = characteristics["performance_indicators"]["speed"]
        
        if time_req == "fast" and speed_score > 0.7:
            score += 0.25
        elif time_req == "medium" and speed_score > 0.5:
            score += 0.25
        elif time_req == "slow" and speed_score > 0.3:
            score += 0.25
        
        # Kalite gereksinimi
        quality_req = analysis["quality_requirement"]
        accuracy_score = characteristics["performance_indicators"]["accuracy"]
        
        if quality_req == "high" and accuracy_score > 0.8:
            score += 0.25
        elif quality_req == "medium" and accuracy_score > 0.6:
            score += 0.25
        elif quality_req == "low" and accuracy_score > 0.4:
            score += 0.25
        
        # Özel durumlar
        if analysis["multi_objective"] and algo_name in ["nsga_ii", "hybrid_cp_sat_nsga", "genetic_algorithm"]:
            score += 0.1
        
        if analysis["priority_focus"] and algo_name == "lexicographic":
            score += 0.15
        
        if analysis["constraint_complexity"] == "very_high" and algo_name in ["cp_sat", "hybrid_cp_sat_nsga"]:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _complexity_compatibility(self, algo_complexity: ProblemComplexity, 
                                problem_complexity: ProblemComplexity) -> bool:
        """Algoritma ve problem karmaşıklığı uyumluluğunu kontrol eder"""
        complexity_order = [ProblemComplexity.LOW, ProblemComplexity.MEDIUM, 
                          ProblemComplexity.HIGH, ProblemComplexity.VERY_HIGH]
        
        algo_idx = complexity_order.index(algo_complexity)
        problem_idx = complexity_order.index(problem_complexity)
        
        # Algoritma problemi çözebilmeli ama çok fazla overkill olmamalı
        return algo_idx >= problem_idx - 1 and algo_idx <= problem_idx + 1
    
    def _generate_reasoning(self, algo_name: str, characteristics: Dict[str, Any], 
                          analysis: Dict[str, Any]) -> str:
        """Algoritma için gerekçe üretir"""
        reasoning_parts = []
        
        # Temel güçlü yönler
        strengths = characteristics["strengths"]
        reasoning_parts.append(f"Güçlü yönleri: {', '.join(strengths[:2])}")
        
        # Problem boyutu uyumu
        if characteristics["complexity"] == analysis["problem_size"]:
            reasoning_parts.append(f"Problem boyutu ({analysis['problem_size'].value}) için ideal")
        
        # Performans beklentisi
        perf = characteristics["performance_indicators"]
        if perf["accuracy"] > 0.8:
            reasoning_parts.append("Yüksek kalite çözümler üretir")
        if perf["speed"] > 0.7:
            reasoning_parts.append("Hızlı çözüm sağlar")
        
        # Özel durumlar
        if algo_name == "cp_sat" and analysis["constraint_complexity"] in ["high", "very_high"]:
            reasoning_parts.append("Karmaşık kurallar için güvenilir")
        
        if algo_name == "hybrid_cp_sat_nsga" and analysis["multi_objective"]:
            reasoning_parts.append("Çok amaçlı optimizasyon için ideal")
        
        return ". ".join(reasoning_parts) + "."
    
    def get_algorithm_comparison(self, problem_context: Dict[str, Any]) -> Dict[str, Any]:
        """Algoritmaların karşılaştırmalı analizini döndürür"""
        recommendations = self.recommend_algorithm(problem_context)
        
        comparison = {
            "problem_analysis": self._analyze_problem_context(problem_context),
            "recommendations": [
                {
                    "algorithm": rec.algorithm_name,
                    "confidence": rec.confidence,
                    "reasoning": rec.reasoning,
                    "performance": rec.expected_performance
                }
                for rec in recommendations
            ],
            "top_recommendation": recommendations[0].algorithm_name if recommendations else None,
            "alternative_options": [rec.algorithm_name for rec in recommendations[1:3]]
        }
        
        return comparison
