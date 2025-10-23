"""
User-based recommendation service for algorithm selection
"""

from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.algorithm import AlgorithmRun, AlgorithmType
from app.models.project import Project
from app.algorithms.factory import AlgorithmFactory
from app.services.cache_service import cache_service
from app.services.parallel_processing_service import parallel_processing_service


class RecommendationService:
    """
    Service for providing user-based algorithm recommendations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.factory = AlgorithmFactory()
        
        # Proje açıklamasına göre algoritma performans ağırlıkları
        self.algorithm_weights = {
            "small_dataset": {
                # Küçük problemler için: Simplex (hızlı), Greedy (basit)
                AlgorithmType.SIMPLEX: 0.9,
                AlgorithmType.GREEDY: 0.8,
                AlgorithmType.SIMULATED_ANNEALING: 0.6,
                AlgorithmType.TABU_SEARCH: 0.5,
                AlgorithmType.GENETIC_ALGORITHM: 0.4,
            },
            "medium_dataset": {
                # Orta problemler için: Simulated Annealing, Tabu Search
                AlgorithmType.SIMULATED_ANNEALING: 0.9,
                AlgorithmType.TABU_SEARCH: 0.8,
                AlgorithmType.GENETIC_ALGORITHM: 0.7,
                AlgorithmType.PSO: 0.6,
                AlgorithmType.HARMONY_SEARCH: 0.5,
            },
            "large_dataset": {
                # Büyük problemler için: NSGA-II, Hibrit modeller
                AlgorithmType.NSGA_II: 0.9,
                AlgorithmType.HYBRID_CP_SAT_NSGA: 0.8,
                AlgorithmType.GENETIC_ALGORITHM: 0.7,
                AlgorithmType.PSO: 0.6,
                AlgorithmType.FIREFLY: 0.5,
            },
            "constraint_critical": {
                # Kısıt programlama gerektiren durumlar için
                AlgorithmType.CP_SAT: 0.9,
                AlgorithmType.HYBRID_CP_SAT_NSGA: 0.8,
                AlgorithmType.LEXICOGRAPHIC: 0.7,
                AlgorithmType.DEEP_SEARCH: 0.6,
            },
            "multi_objective": {
                # Çok amaçlı optimizasyon için
                AlgorithmType.NSGA_II: 0.9,
                AlgorithmType.HYBRID_CP_SAT_NSGA: 0.8,
                AlgorithmType.LEXICOGRAPHIC: 0.7,
                AlgorithmType.GENETIC_ALGORITHM: 0.6,
            },
            "final_vs_makeup": {
                # Final vs bütünleme ayrımı için
                AlgorithmType.GREEDY: 0.9,  # Bütünleme için hızlı çözüm
                AlgorithmType.SIMPLEX: 0.8,  # Final için optimal çözüm
                AlgorithmType.SIMULATED_ANNEALING: 0.6,
            }
        }
    
    async def recommend_algorithm(self, user_id: int, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Proje açıklamasına göre en uygun algoritmayı önerir.
        "En uygun algoritmayı öner" özelliği implementasyonu.
        Performans optimizasyonu ile cache ve parallel processing kullanır.
        
        Args:
            user_id: ID of the user requesting recommendation
            problem_data: Problem characteristics (projects, instructors, etc.)
            
        Returns:
            Recommendation with algorithm type and reasoning
        """
        try:
            # Check cache first
            cached_recommendation = await cache_service.get_cached_algorithm_recommendation(user_id, problem_data)
            if cached_recommendation:
                logger.info(f"Cache hit for algorithm recommendation for user {user_id}")
                return cached_recommendation
            
            # Get user's historical performance (with cache)
            user_history = await self._get_user_history_cached(user_id)
            
            # Analyze problem characteristics (with parallel processing)
            problem_analysis = await self._analyze_problem_parallel(problem_data)
            
            # Calculate algorithm scores
            algorithm_scores = self._calculate_algorithm_scores(
                problem_analysis, user_history
            )
            
            # Get top recommendation
            best_algorithm = max(algorithm_scores.items(), key=lambda x: x[1])
            
            # Generate recommendation reasoning
            reasoning = self._generate_reasoning(
                best_algorithm[0], problem_analysis, user_history
            )
            
            recommendation = {
                "recommended_algorithm": best_algorithm[0].value,
                "confidence_score": best_algorithm[1],
                "reasoning": reasoning,
                "all_scores": {
                    algo.value: score for algo, score in algorithm_scores.items()
                },
                "problem_analysis": problem_analysis,
                "timestamp": datetime.utcnow().isoformat(),
                "cached": False
            }
            
            # Cache the recommendation
            await cache_service.cache_algorithm_recommendation(user_id, problem_data, recommendation)
            
            return recommendation
            
        except Exception as e:
            # Fallback to greedy algorithm
            fallback_recommendation = {
                "recommended_algorithm": AlgorithmType.GREEDY.value,
                "confidence_score": 0.5,
                "reasoning": f"Fallback recommendation due to error: {str(e)}",
                "all_scores": {AlgorithmType.GREEDY.value: 0.5},
                "problem_analysis": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat(),
                "cached": False
            }
            return fallback_recommendation
    
    def _get_user_history(self, user_id: int) -> Dict[str, Any]:
        """Get user's algorithm performance history."""
        # Get last 30 days of algorithm runs
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        runs = self.db.query(AlgorithmRun).filter(
            AlgorithmRun.started_at >= thirty_days_ago
        ).all()
        
        # Calculate performance metrics
        algorithm_performance = {}
        for run in runs:
            algo_type = run.algorithm_type
            if algo_type not in algorithm_performance:
                algorithm_performance[algo_type] = {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "avg_execution_time": 0,
                    "avg_score": 0,
                    "scores": []
                }
            
            perf = algorithm_performance[algo_type]
            perf["total_runs"] += 1
            
            if run.status == "completed":
                perf["successful_runs"] += 1
                if run.execution_time:
                    perf["avg_execution_time"] = (
                        (perf["avg_execution_time"] * (perf["successful_runs"] - 1) + 
                         run.execution_time) / perf["successful_runs"]
                    )
                if run.score:
                    perf["scores"].append(run.score)
        
        # Calculate average scores
        for algo_type, perf in algorithm_performance.items():
            if perf["scores"]:
                perf["avg_score"] = np.mean(perf["scores"])
        
        return {
            "algorithm_performance": algorithm_performance,
            "total_runs": len(runs),
            "period_days": 30
        }
    
    def _analyze_problem(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Proje açıklamasına göre problem karakteristiklerini analiz eder.
        """
        projects = problem_data.get("projects", [])
        instructors = problem_data.get("instructors", [])
        classrooms = problem_data.get("classrooms", [])
        timeslots = problem_data.get("timeslots", [])
        
        # Proje açıklamasına göre problem boyutu hesaplama
        total_variables = len(projects) * len(classrooms) * len(timeslots)
        
        # Proje açıklamasına göre dataset boyutu kategorisi
        if total_variables <= 100:
            dataset_size = "small_dataset"
        elif total_variables <= 1000:
            dataset_size = "medium_dataset"
        else:
            dataset_size = "large_dataset"
        
        # Proje açıklamasına göre karmaşıklık analizi
        complexity_score = self._calculate_complexity_score(
            projects, instructors, classrooms, timeslots
        )
        
        # Proje açıklamasına göre kısıt analizi
        has_strict_constraints = self._has_strict_constraints(projects)
        
        # Final vs bütünleme analizi
        is_makeup_session = problem_data.get("is_makeup", False)
        
        # Çok amaçlı optimizasyon gereksinimi
        requires_multi_objective = self._requires_multi_objective_optimization(projects, instructors)
        
        return {
            "dataset_size": dataset_size,
            "total_variables": total_variables,
            "complexity_score": complexity_score,
            "has_strict_constraints": has_strict_constraints,
            "is_makeup_session": is_makeup_session,
            "requires_multi_objective": requires_multi_objective,
            "project_count": len(projects),
            "instructor_count": len(instructors),
            "classroom_count": len(classrooms),
            "timeslot_count": len(timeslots),
            "bitirme_project_count": len([p for p in projects if p.get("type") == "bitirme"]),
            "ara_project_count": len([p for p in projects if p.get("type") == "ara"])
        }
    
    def _calculate_complexity_score(self, projects: List, instructors: List, 
                                  classrooms: List, timeslots: List) -> float:
        """Calculate problem complexity score."""
        # Base complexity from variable count
        base_complexity = len(projects) * len(classrooms) * len(timeslots)
        
        # Add complexity for constraint types
        constraint_complexity = 0
        
        # Check for different project types
        project_types = set(p.get("type", "ara") for p in projects)
        if len(project_types) > 1:
            constraint_complexity += 10
        
        # Check for instructor load balancing requirements
        if len(instructors) > 1:
            constraint_complexity += 5
        
        # Check for time constraints
        if len(timeslots) > 8:  # More than one day
            constraint_complexity += 15
        
        total_complexity = base_complexity + constraint_complexity
        
        # Normalize to 0-1 scale
        return min(total_complexity / 1000, 1.0)
    
    def _has_strict_constraints(self, projects: List) -> bool:
        """Check if problem has strict constraints."""
        # Check for bitirme projects (require at least 2 instructors)
        for project in projects:
            if project.get("type") == "bitirme":
                return True
        
        # Check for time constraints
        # Add more constraint checks as needed
        
        return False
    
    def _requires_multi_objective_optimization(self, projects: List, instructors: List) -> bool:
        """
        Çok amaçlı optimizasyon gereksinimi kontrol eder.
        Proje açıklamasına göre: 5 farklı amaç fonksiyonu (yük dengesi, sınıf geçişi, saat bütünlüğü, oturum minimizasyonu, kural uyumu)
        """
        # Çok amaçlı optimizasyon gerektiren durumlar:
        
        # 1. Birden fazla hoca varsa yük dengesi önemli
        if len(instructors) > 3:
            return True
        
        # 2. Bitirme projeleri varsa (en az 2 hoca gerektirir)
        bitirme_projects = [p for p in projects if p.get("type") == "bitirme"]
        if len(bitirme_projects) > 0:
            return True
        
        # 3. Çok sayıda proje varsa (5'ten fazla)
        if len(projects) > 5:
            return True
        
        # 4. Karma proje türleri varsa (bitirme + ara)
        project_types = set(p.get("type", "ara") for p in projects)
        if len(project_types) > 1:
            return True
        
        return False
    
    def _calculate_algorithm_scores(self, problem_analysis: Dict[str, Any], 
                                  user_history: Dict[str, Any]) -> Dict[AlgorithmType, float]:
        """
        Proje açıklamasına göre algoritma skorlarını hesaplar.
        """
        scores = {}
        
        # Proje açıklamasına göre temel ağırlıklar
        dataset_size = problem_analysis["dataset_size"]
        complexity = problem_analysis["complexity_score"]
        has_strict_constraints = problem_analysis["has_strict_constraints"]
        is_makeup_session = problem_analysis["is_makeup_session"]
        requires_multi_objective = problem_analysis["requires_multi_objective"]
        
        # Temel ağırlıkları al
        base_weights = self.algorithm_weights[dataset_size].copy()
        
        # Proje açıklamasına göre ağırlık ayarlamaları
        
        # 1. Karmaşıklığa göre ayarlama
        if complexity > 0.7:  # Yüksek karmaşıklık
            # Daha güçlü algoritmaları tercih et
            base_weights[AlgorithmType.NSGA_II] = base_weights.get(AlgorithmType.NSGA_II, 0.5) * 1.2
            base_weights[AlgorithmType.HYBRID_CP_SAT_NSGA] = base_weights.get(AlgorithmType.HYBRID_CP_SAT_NSGA, 0.5) * 1.2
            base_weights[AlgorithmType.DEEP_SEARCH] = base_weights.get(AlgorithmType.DEEP_SEARCH, 0.5) * 1.1
        elif complexity < 0.3:  # Düşük karmaşıklık
            # Daha hızlı algoritmaları tercih et
            base_weights[AlgorithmType.GREEDY] = base_weights.get(AlgorithmType.GREEDY, 0.5) * 1.2
            base_weights[AlgorithmType.SIMPLEX] = base_weights.get(AlgorithmType.SIMPLEX, 0.5) * 1.2
        
        # 2. Kısıtlara göre ayarlama
        if has_strict_constraints:
            # Kısıt sağlayan algoritmaları tercih et
            base_weights[AlgorithmType.CP_SAT] = base_weights.get(AlgorithmType.CP_SAT, 0.5) * 1.3
            base_weights[AlgorithmType.HYBRID_CP_SAT_NSGA] = base_weights.get(AlgorithmType.HYBRID_CP_SAT_NSGA, 0.5) * 1.3
            base_weights[AlgorithmType.LEXICOGRAPHIC] = base_weights.get(AlgorithmType.LEXICOGRAPHIC, 0.5) * 1.2
        
        # 3. Final vs bütünleme ayarlaması
        if is_makeup_session:
            # Bütünleme için hızlı çözüm algoritmaları
            base_weights.update(self.algorithm_weights["final_vs_makeup"])
        
        # 4. Çok amaçlı optimizasyon gereksinimi
        if requires_multi_objective:
            # Çok amaçlı algoritmaları tercih et
            multi_obj_weights = self.algorithm_weights["multi_objective"]
            for algo_type, weight in multi_obj_weights.items():
                base_weights[algo_type] = base_weights.get(algo_type, 0.5) * 1.2
        
        # 5. Kullanıcı geçmişine göre ayarlama
        user_performance = user_history.get("algorithm_performance", {})
        for algo_type, weight in base_weights.items():
            if algo_type in user_performance:
                perf = user_performance[algo_type]
                success_rate = perf["successful_runs"] / max(perf["total_runs"], 1)
                avg_score = perf.get("avg_score", 0.5)
                
                # Kullanıcının bu algoritma ile başarısına göre boost
                history_boost = (success_rate * 0.3 + avg_score * 0.2)
                weight = weight * (1 + history_boost)
            
            scores[algo_type] = min(weight, 1.0)  # 1.0 ile sınırla
        
        # Tüm algoritmaların skoru olduğundan emin ol
        for algo_type in AlgorithmType:
            if algo_type not in scores:
                scores[algo_type] = 0.3  # Varsayılan skor
        
        return scores
    
    def _generate_reasoning(self, recommended_algorithm: AlgorithmType, 
                          problem_analysis: Dict[str, Any], 
                          user_history: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for the recommendation."""
        dataset_size = problem_analysis["dataset_size"]
        complexity = problem_analysis["complexity_score"]
        has_strict_constraints = problem_analysis["has_strict_constraints"]
        
        reasons = []
        
        # Dataset size reasoning
        if dataset_size == "small_dataset":
            reasons.append("Small problem size favors exact algorithms")
        elif dataset_size == "medium_dataset":
            reasons.append("Medium problem size is ideal for metaheuristic algorithms")
        else:
            reasons.append("Large problem size requires efficient optimization algorithms")
        
        # Complexity reasoning
        if complexity > 0.7:
            reasons.append("High complexity problem requires robust optimization")
        elif complexity < 0.3:
            reasons.append("Simple problem allows for fast greedy approaches")
        
        # Constraint reasoning
        if has_strict_constraints:
            reasons.append("Strict constraints require constraint-satisfying algorithms")
        
        # User history reasoning
        user_performance = user_history.get("algorithm_performance", {})
        if recommended_algorithm in user_performance:
            perf = user_performance[recommended_algorithm]
            if perf["total_runs"] > 0:
                success_rate = perf["successful_runs"] / perf["total_runs"]
                if success_rate > 0.8:
                    reasons.append("You have had excellent success with this algorithm")
                elif success_rate > 0.6:
                    reasons.append("You have had good success with this algorithm")
        
        return "; ".join(reasons) + "."
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user's algorithm preferences based on history."""
        history = self._get_user_history(user_id)
        
        # Find user's most successful algorithms
        algorithm_performance = history.get("algorithm_performance", {})
        
        if not algorithm_performance:
            return {
                "preferred_algorithms": [],
                "success_rates": {},
                "avg_execution_times": {},
                "recommendations": "No historical data available"
            }
        
        # Sort algorithms by success rate
        sorted_algorithms = sorted(
            algorithm_performance.items(),
            key=lambda x: x[1]["successful_runs"] / max(x[1]["total_runs"], 1),
            reverse=True
        )
        
        preferred = [algo.value for algo, _ in sorted_algorithms[:3]]
        success_rates = {
            algo.value: perf["successful_runs"] / max(perf["total_runs"], 1)
            for algo, perf in algorithm_performance.items()
        }
        avg_times = {
            algo.value: perf["avg_execution_time"]
            for algo, perf in algorithm_performance.items()
            if perf["avg_execution_time"] > 0
        }
        
        return {
            "preferred_algorithms": preferred,
            "success_rates": success_rates,
            "avg_execution_times": avg_times,
            "total_runs": history["total_runs"],
            "period_days": history["period_days"]
        }
    
    async def _get_user_history_cached(self, user_id: int) -> Dict[str, Any]:
        """Get user's algorithm performance history with caching."""
        # Check cache first
        cached_history = await cache_service.get_cached_user_history(user_id)
        if cached_history:
            return cached_history
        
        # Get from database
        history = self._get_user_history(user_id)
        
        # Cache the result
        await cache_service.cache_user_history(user_id, history)
        
        return history
    
    async def _analyze_problem_parallel(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze problem characteristics using parallel processing."""
        # Check cache first
        cached_analysis = await cache_service.get_cached_problem_analysis(problem_data)
        if cached_analysis:
            return cached_analysis
        
        # Run analysis in parallel
        analysis = await parallel_processing_service.run_problem_analysis_parallel(problem_data)
        
        # Add additional analysis
        analysis.update({
            "dataset_size": self._determine_dataset_size(analysis["project_count"], analysis["classroom_count"], analysis["timeslot_count"]),
            "is_makeup_session": problem_data.get("is_makeup", False)
        })
        
        # Cache the result
        await cache_service.cache_problem_analysis(problem_data, analysis)
        
        return analysis
    
    def _determine_dataset_size(self, project_count: int, classroom_count: int, timeslot_count: int) -> str:
        """Determine dataset size category."""
        total_variables = project_count * classroom_count * timeslot_count
        
        if total_variables <= 100:
            return "small_dataset"
        elif total_variables <= 1000:
            return "medium_dataset"
        else:
            return "large_dataset"
