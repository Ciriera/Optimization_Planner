"""
Objective Function Weights Service
Manages configurable weights for the multi-objective optimization function
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.cache_service import cache_service
import logging

logger = logging.getLogger(__name__)


class ObjectiveWeightsService:
    """Service for managing objective function weights"""
    
    def __init__(self):
        # Default weights as specified in project requirements
        self.default_weights = {
            "load_balance": 0.3,          # W1: Yük dengesi
            "classroom_changes": 0.3,     # W2: Sınıf geçişi azlığı  
            "time_efficiency": 0.2,       # W3: Saat bütünlüğü
            "session_minimization": 0.1,  # W4: Oturum sayısı minimizasyonu
            "rule_compliance": 0.1        # W5: Kurallara uyum
        }
        
        # Objective descriptions
        self.objective_descriptions = {
            "load_balance": {
                "name": "Yük Dengesi",
                "description": "Öğretim elemanları arasındaki toplam yükün dengeli dağıtılması",
                "calculation": "Gini katsayısı ve standart sapma ile hesaplanır",
                "target": "minimize",  # Lower is better
                "range": [0.0, 1.0]
            },
            "classroom_changes": {
                "name": "Sınıf Değişimi",
                "description": "Öğretim elemanlarının sınıf değiştirme sayısının minimize edilmesi",
                "calculation": "Toplam sınıf değişim sayısı",
                "target": "minimize",  # Lower is better
                "range": [0, 100]
            },
            "time_efficiency": {
                "name": "Saat Bütünlüğü",
                "description": "Öğretim elemanlarının saatlik dağılımlarının uniform olması",
                "calculation": "Aralıksız oturum dizileri oranı",
                "target": "maximize",  # Higher is better
                "range": [0.0, 1.0]
            },
            "session_minimization": {
                "name": "Oturum Minimizasyonu",
                "description": "Toplam oturum sayısının minimize edilmesi",
                "calculation": "Toplam zaman dilimi sayısı",
                "target": "minimize",  # Lower is better
                "range": [1, 100]
            },
            "rule_compliance": {
                "name": "Kural Uyumu",
                "description": "Kurallara uyum (eksik hoca/yanlış yapı olmaması)",
                "calculation": "İhlal edilen kural sayısı",
                "target": "minimize",  # Lower is better
                "range": [0, 100]
            }
        }
    
    async def get_current_weights(self) -> Dict[str, Any]:
        """Mevcut ağırlık konfigürasyonunu getirir"""
        
        return {
            "weights": self.default_weights.copy(),
            "descriptions": self.objective_descriptions,
            "total_weight": sum(self.default_weights.values()),
            "is_normalized": self._is_normalized(self.default_weights)
        }
    
    async def update_weights(self, new_weights: Dict[str, float]) -> Dict[str, Any]:
        """Ağırlıkları günceller"""
        
        try:
            # Validation
            validation_result = self._validate_weights(new_weights)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": "Weight validation failed",
                    "errors": validation_result["errors"]
                }
            
            # Normalize weights
            normalized_weights = self._normalize_weights(new_weights)
            
            # Update weights
            self.default_weights.update(normalized_weights)
            
            return {
                "success": True,
                "message": "Weights updated successfully",
                "updated_weights": self.default_weights.copy(),
                "normalization_applied": validation_result["needs_normalization"]
            }
            
        except Exception as e:
            logger.error(f"Error updating weights: {str(e)}")
            return {
                "success": False,
                "message": f"Error updating weights: {str(e)}"
            }
    
    def _validate_weights(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """Ağırlıkları validate eder"""
        
        errors = []
        
        # Check if all required objectives are present
        required_objectives = set(self.default_weights.keys())
        provided_objectives = set(weights.keys())
        
        missing_objectives = required_objectives - provided_objectives
        if missing_objectives:
            errors.append(f"Missing objectives: {', '.join(missing_objectives)}")
        
        # Check for unknown objectives
        unknown_objectives = provided_objectives - required_objectives
        if unknown_objectives:
            errors.append(f"Unknown objectives: {', '.join(unknown_objectives)}")
        
        # Check weight values
        for objective, weight in weights.items():
            if not isinstance(weight, (int, float)):
                errors.append(f"Weight for {objective} must be a number")
            elif weight < 0:
                errors.append(f"Weight for {objective} cannot be negative")
            elif weight > 1:
                errors.append(f"Weight for {objective} cannot be greater than 1")
        
        # Check total weight
        total_weight = sum(weights.values())
        needs_normalization = False
        
        if total_weight == 0:
            errors.append("Total weight cannot be zero")
        elif abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
            needs_normalization = True
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "needs_normalization": needs_normalization,
            "total_weight": total_weight
        }
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Ağırlıkları normalize eder"""
        
        total_weight = sum(weights.values())
        if total_weight == 0:
            return self.default_weights.copy()
        
        normalized = {}
        for objective, weight in weights.items():
            normalized[objective] = weight / total_weight
        
        return normalized
    
    def _is_normalized(self, weights: Dict[str, float]) -> bool:
        """Ağırlıkların normalize edilip edilmediğini kontrol eder"""
        
        total_weight = sum(weights.values())
        return abs(total_weight - 1.0) < 0.01
    
    async def calculate_weighted_score(self, objective_scores: Dict[str, float], 
                                     custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Ağırlıklı toplam skor hesaplar.
        Proje açıklamasına göre: Total skor = (W1 * yük dengesi) + (W2 * sınıf geçişi) + (W3 * saat bütünlüğü) + ...
        """
        
        weights = custom_weights if custom_weights else self.default_weights
        
        # Check cache first for weighted score calculation
        cached_result = await cache_service.get_cached_weighted_score(objective_scores, weights)
        if cached_result:
            logger.info("Cache hit for weighted score calculation")
            return cached_result
        
        # Validate objective scores
        validation_result = self._validate_objective_scores(objective_scores)
        if not validation_result["valid"]:
            return {
                "success": False,
                "message": "Objective scores validation failed",
                "errors": validation_result["errors"]
            }
        
        # Calculate weighted score according to project specification formula
        weighted_score = 0.0
        weighted_components = {}
        
        # Proje açıklamasına göre formül: Total skor = (W1 * yük dengesi) + (W2 * sınıf geçişi) + (W3 * saat bütünlüğü) + (W4 * oturum minimizasyonu) + (W5 * kural uyumu)
        for objective, weight in weights.items():
            if objective in objective_scores:
                score = objective_scores[objective]
                
                # Normalize score based on objective type (0-100 arası)
                normalized_score = self._normalize_objective_score(objective, score)
                
                # Apply weight
                weighted_component = weight * normalized_score
                weighted_score += weighted_component
                
                weighted_components[objective] = {
                    "raw_score": score,
                    "normalized_score": normalized_score,
                    "weight": weight,
                    "weighted_component": weighted_component,
                    "description": self.objective_descriptions[objective]["description"]
                }
        
        # Normalize final score to 0-100 range
        final_score = min(100.0, max(0.0, weighted_score))
        
        result = {
            "success": True,
            "total_weighted_score": round(final_score, 4),
            "weighted_components": weighted_components,
            "weights_used": weights,
            "objective_scores": objective_scores,
            "project_specification_formula": "Total skor = (W1 * yük dengesi) + (W2 * sınıf geçişi) + (W3 * saat bütünlüğü) + (W4 * oturum minimizasyonu) + (W5 * kural uyumu)",
            "normalized_final_score": final_score
        }
        
        # Cache the result
        await cache_service.cache_weighted_score(objective_scores, weights, result)
        
        return result
    
    def _validate_objective_scores(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """Objective skorlarını validate eder"""
        
        errors = []
        
        for objective, score in scores.items():
            if objective not in self.default_weights:
                errors.append(f"Unknown objective: {objective}")
                continue
            
            if not isinstance(score, (int, float)):
                errors.append(f"Score for {objective} must be a number")
                continue
            
            # Check range
            expected_range = self.objective_descriptions[objective]["range"]
            if score < expected_range[0] or score > expected_range[1]:
                errors.append(f"Score for {objective} ({score}) is outside expected range {expected_range}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _normalize_objective_score(self, objective: str, score: float) -> float:
        """Objective skorunu normalize eder"""
        
        objective_info = self.objective_descriptions[objective]
        expected_range = objective_info["range"]
        target = objective_info["target"]
        
        # Normalize to 0-1 range
        range_size = expected_range[1] - expected_range[0]
        if range_size == 0:
            return 1.0
        
        normalized = (score - expected_range[0]) / range_size
        
        # Apply target (minimize objectives are inverted)
        if target == "minimize":
            normalized = 1.0 - normalized
        
        # Clamp to 0-1 range
        return max(0.0, min(1.0, normalized))
    
    async def get_weight_recommendations(self, problem_context: Dict[str, Any]) -> Dict[str, Any]:
        """Problem context'e göre ağırlık önerileri üretir"""
        
        recommendations = {}
        
        # Problem size based recommendations
        project_count = problem_context.get("project_count", 0)
        instructor_count = problem_context.get("instructor_count", 0)
        
        if project_count > 50:
            recommendations["session_minimization"] = {
                "current_weight": self.default_weights["session_minimization"],
                "recommended_weight": 0.15,
                "reason": "Large project count requires more focus on session minimization"
            }
        
        if instructor_count < 10:
            recommendations["load_balance"] = {
                "current_weight": self.default_weights["load_balance"],
                "recommended_weight": 0.4,
                "reason": "Few instructors require more emphasis on load balancing"
            }
        
        # Priority based recommendations
        if problem_context.get("priority_focus") == "classroom_changes":
            recommendations["classroom_changes"] = {
                "current_weight": self.default_weights["classroom_changes"],
                "recommended_weight": 0.5,
                "reason": "Classroom change minimization is the priority"
            }
        
        if problem_context.get("priority_focus") == "time_efficiency":
            recommendations["time_efficiency"] = {
                "current_weight": self.default_weights["time_efficiency"],
                "recommended_weight": 0.4,
                "reason": "Time efficiency is the priority"
            }
        
        return {
            "recommendations": recommendations,
            "current_weights": self.default_weights.copy(),
            "context": problem_context
        }
    
    async def compare_weight_scenarios(self, objective_scores: Dict[str, float], 
                                     weight_scenarios: List[Dict[str, float]]) -> Dict[str, Any]:
        """Farklı ağırlık senaryolarını karşılaştırır"""
        
        results = []
        
        for i, weights in enumerate(weight_scenarios):
            scenario_result = await self.calculate_weighted_score(objective_scores, weights)
            
            if scenario_result["success"]:
                results.append({
                    "scenario_id": i + 1,
                    "weights": weights,
                    "total_score": scenario_result["total_weighted_score"],
                    "weighted_components": scenario_result["weighted_components"]
                })
        
        # Sort by total score
        results.sort(key=lambda x: x["total_score"], reverse=True)
        
        return {
            "scenarios": results,
            "best_scenario": results[0] if results else None,
            "objective_scores": objective_scores
        }
    
    async def get_weight_sensitivity_analysis(self, objective_scores: Dict[str, float]) -> Dict[str, Any]:
        """Ağırlık hassasiyet analizi yapar"""
        
        sensitivity_analysis = {}
        
        for objective in self.default_weights.keys():
            # Test with increased weight
            increased_weights = self.default_weights.copy()
            increased_weights[objective] = min(1.0, increased_weights[objective] + 0.2)
            increased_weights = self._normalize_weights(increased_weights)
            
            increased_result = await self.calculate_weighted_score(objective_scores, increased_weights)
            
            # Test with decreased weight
            decreased_weights = self.default_weights.copy()
            decreased_weights[objective] = max(0.0, decreased_weights[objective] - 0.2)
            decreased_weights = self._normalize_weights(decreased_weights)
            
            decreased_result = await self.calculate_weighted_score(objective_scores, decreased_weights)
            
            # Current result
            current_result = await self.calculate_weighted_score(objective_scores)
            
            sensitivity_analysis[objective] = {
                "current_weight": self.default_weights[objective],
                "current_score": current_result["total_weighted_score"],
                "increased_weight": increased_weights[objective],
                "increased_score": increased_result["total_weighted_score"],
                "decreased_weight": decreased_weights[objective],
                "decreased_score": decreased_result["total_weighted_score"],
                "sensitivity": abs(increased_result["total_weighted_score"] - decreased_result["total_weighted_score"])
            }
        
        return {
            "sensitivity_analysis": sensitivity_analysis,
            "most_sensitive": max(sensitivity_analysis.items(), key=lambda x: x[1]["sensitivity"])[0],
            "least_sensitive": min(sensitivity_analysis.items(), key=lambda x: x[1]["sensitivity"])[0]
        }
