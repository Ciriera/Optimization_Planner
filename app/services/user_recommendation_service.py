"""
User-Based Recommendation Service
Proje açıklamasına göre: Kullanıcı bazlı öneri sistemi
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.models.user import User
from app.models.algorithm import AlgorithmRun
from app.models.project import Project
from app.models.instructor import Instructor
from app.models.algorithm import AlgorithmType
from app.services.cache_service import cache_service
from app.services.parallel_processing_service import parallel_processing_service

logger = logging.getLogger(__name__)

class UserRecommendationService:
    """
    Kullanıcı bazlı öneri sistemi.
    Proje açıklamasına göre: Kullanıcı bazlı öneri sistemi
    """
    
    def __init__(self):
        self.cache_service = cache_service
        self.parallel_processing_service = parallel_processing_service
    
    async def get_personalized_algorithm_recommendation(self, user_id: int, 
                                                      problem_data: Dict[str, Any],
                                                      db: AsyncSession) -> Dict[str, Any]:
        """
        Kullanıcıya özelleştirilmiş algoritma önerisi getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            problem_data: Problem verileri
            db: Database session
            
        Returns:
            Personalized algorithm recommendation
        """
        try:
            logger.info(f"Getting personalized algorithm recommendation for user: {user_id}")
            
            # 1. Kullanıcı geçmişini analiz et
            user_history = await self._analyze_user_history(user_id, db)
            
            # 2. Problem karakteristiklerini analiz et
            problem_analysis = await self._analyze_problem_characteristics(problem_data)
            
            # 3. Benzer kullanıcıların başarılı algoritmalarını bul
            similar_users = await self._find_similar_users(user_id, user_history, db)
            
            # 4. Algoritma performans verilerini al
            algorithm_performance = await self._get_algorithm_performance_data(db)
            
            # 5. Kişiselleştirilmiş öneri oluştur
            recommendation = await self._create_personalized_recommendation(
                user_history, problem_analysis, similar_users, algorithm_performance
            )
            
            # 6. Öneriyi cache'le
            await self._cache_recommendation(user_id, problem_data, recommendation)
            
            # 7. Kullanıcı davranışını kaydet
            await self._record_user_behavior(user_id, problem_data, recommendation, db)
            
            return {
                "success": True,
                "recommendation": recommendation,
                "confidence_score": recommendation.get("confidence", 0),
                "reasoning": recommendation.get("reasoning", ""),
                "message": "Kişiselleştirilmiş algoritma önerisi hazırlandı"
            }
            
        except Exception as e:
            logger.error(f"Error getting personalized algorithm recommendation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Kişiselleştirilmiş öneri oluşturulamadı"
            }
    
    async def get_user_performance_insights(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        Kullanıcının performans içgörülerini getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            db: Database session
            
        Returns:
            User performance insights
        """
        try:
            logger.info(f"Getting performance insights for user: {user_id}")
            
            # 1. Kullanıcının algoritma kullanım geçmişi
            algorithm_usage = await self._get_algorithm_usage_history(user_id, db)
            
            # 2. Başarı oranları
            success_rates = await self._calculate_success_rates(user_id, db)
            
            # 3. En iyi performans gösterdiği problem türleri
            best_performing_problems = await self._get_best_performing_problems(user_id, db)
            
            # 4. İyileştirme önerileri
            improvement_suggestions = await self._generate_improvement_suggestions(
                algorithm_usage, success_rates, best_performing_problems
            )
            
            # 5. Karşılaştırmalı analiz
            comparative_analysis = await self._get_comparative_analysis(user_id, db)
            
            return {
                "success": True,
                "user_id": user_id,
                "algorithm_usage": algorithm_usage,
                "success_rates": success_rates,
                "best_performing_problems": best_performing_problems,
                "improvement_suggestions": improvement_suggestions,
                "comparative_analysis": comparative_analysis,
                "message": "Performans içgörüleri başarıyla oluşturuldu"
            }
            
        except Exception as e:
            logger.error(f"Error getting user performance insights: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Performans içgörüleri oluşturulamadı"
            }
    
    async def get_smart_defaults(self, user_id: int, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kullanıcı için akıllı varsayılan değerler önerir.
        
        Args:
            user_id: Kullanıcı ID'si
            problem_data: Problem verileri
            
        Returns:
            Smart default parameters
        """
        try:
            logger.info(f"Getting smart defaults for user: {user_id}")
            
            # 1. Kullanıcının geçmiş tercihlerini analiz et
            user_preferences = await self._analyze_user_preferences(user_id)
            
            # 2. Problem boyutuna göre optimal parametreleri hesapla
            optimal_params = await self._calculate_optimal_parameters(problem_data)
            
            # 3. Kullanıcı geçmişi ile optimal parametreleri birleştir
            smart_defaults = await self._merge_preferences_and_optimal(user_preferences, optimal_params)
            
            return {
                "success": True,
                "smart_defaults": smart_defaults,
                "reasoning": "Kullanıcı geçmişi ve problem karakteristiklerine dayalı öneriler",
                "confidence": 0.85,
                "message": "Akıllı varsayılan değerler hazırlandı"
            }
            
        except Exception as e:
            logger.error(f"Error getting smart defaults: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Akıllı varsayılan değerler oluşturulamadı"
            }
    
    async def _analyze_user_history(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Kullanıcı geçmişini analiz et"""
        try:
            # Son 30 günlük algoritma çalıştırmalarını getir
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            result = await db.execute(
                select(AlgorithmRun)
                .filter(
                    and_(
                        AlgorithmRun.user_id == user_id,
                        AlgorithmRun.created_at >= thirty_days_ago
                    )
                )
                .order_by(desc(AlgorithmRun.created_at))
            )
            recent_runs = result.scalars().all()
            
            # İstatistikleri hesapla
            total_runs = len(recent_runs)
            successful_runs = sum(1 for run in recent_runs if run.status == "completed")
            
            # En çok kullanılan algoritmalar
            algorithm_counts = {}
            for run in recent_runs:
                algo_name = run.algorithm_type.value if run.algorithm_type else "unknown"
                algorithm_counts[algo_name] = algorithm_counts.get(algo_name, 0) + 1
            
            most_used_algorithm = max(algorithm_counts.items(), key=lambda x: x[1]) if algorithm_counts else ("none", 0)
            
            # Ortalama çalıştırma süresi
            avg_duration = sum(
                (run.completed_at - run.started_at).total_seconds() 
                for run in recent_runs 
                if run.completed_at and run.started_at
            ) / total_runs if total_runs > 0 else 0
            
            return {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "success_rate": successful_runs / total_runs if total_runs > 0 else 0,
                "most_used_algorithm": most_used_algorithm[0],
                "algorithm_frequency": algorithm_counts,
                "average_duration": avg_duration,
                "last_run_date": recent_runs[0].created_at.isoformat() if recent_runs else None,
                "active_days": len(set(run.created_at.date() for run in recent_runs))
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing user history: {str(e)}")
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "success_rate": 0,
                "most_used_algorithm": "none",
                "algorithm_frequency": {},
                "average_duration": 0,
                "last_run_date": None,
                "active_days": 0
            }
    
    async def _analyze_problem_characteristics(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """Problem karakteristiklerini analiz et"""
        try:
            projects = problem_data.get("projects", [])
            instructors = problem_data.get("instructors", [])
            classrooms = problem_data.get("classrooms", [])
            timeslots = problem_data.get("timeslots", [])
            
            # Problem boyutu
            problem_size = len(projects)
            
            # Proje türü dağılımı
            bitirme_count = sum(1 for p in projects if p.get("type") == "bitirme")
            ara_count = len(projects) - bitirme_count
            
            # Hoca türü dağılımı
            instructor_count = sum(1 for i in instructors if i.get("type") == "instructor")
            assistant_count = len(instructors) - instructor_count
            
            # Komplekslik skoru (0-1)
            complexity = min(1.0, (problem_size * len(instructors)) / (len(classrooms) * len(timeslots)))
            
            # Zaman kısıtları
            has_time_constraints = any(
                timeslot.get("session_type") in ["morning", "afternoon"] 
                for timeslot in timeslots
            )
            
            return {
                "problem_size": problem_size,
                "bitirme_count": bitirme_count,
                "ara_count": ara_count,
                "instructor_count": instructor_count,
                "assistant_count": assistant_count,
                "classroom_count": len(classrooms),
                "timeslot_count": len(timeslots),
                "complexity": complexity,
                "has_time_constraints": has_time_constraints,
                "problem_type": self._classify_problem_type(problem_size, complexity, bitirme_count, ara_count)
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing problem characteristics: {str(e)}")
            return {
                "problem_size": 0,
                "bitirme_count": 0,
                "ara_count": 0,
                "instructor_count": 0,
                "assistant_count": 0,
                "classroom_count": 0,
                "timeslot_count": 0,
                "complexity": 0,
                "has_time_constraints": False,
                "problem_type": "unknown"
            }
    
    def _classify_problem_type(self, problem_size: int, complexity: float, 
                             bitirme_count: int, ara_count: int) -> str:
        """Problem türünü sınıflandır"""
        if problem_size < 20:
            return "small"
        elif problem_size < 50:
            return "medium"
        else:
            return "large"
    
    async def _find_similar_users(self, user_id: int, user_history: Dict[str, Any], 
                                db: AsyncSession) -> List[Dict[str, Any]]:
        """Benzer kullanıcıları bul"""
        try:
            # Benzer problem boyutları ve başarı oranları olan kullanıcıları bul
            target_success_rate = user_history.get("success_rate", 0.5)
            target_active_days = user_history.get("active_days", 0)
            
            # Tüm kullanıcıların istatistiklerini getir
            result = await db.execute(
                select(User.id, User.username, func.count(AlgorithmRun.id).label('total_runs'))
                .join(AlgorithmRun, User.id == AlgorithmRun.user_id, isouter=True)
                .group_by(User.id, User.username)
                .having(func.count(AlgorithmRun.id) > 0)
            )
            all_users = result.fetchall()
            
            similar_users = []
            for user_data in all_users:
                if user_data.id == user_id:
                    continue
                
                # Benzerlik skoru hesapla
                similarity_score = self._calculate_user_similarity(
                    user_history, user_data, target_success_rate, target_active_days
                )
                
                if similarity_score > 0.6:  # %60 benzerlik eşiği
                    similar_users.append({
                        "user_id": user_data.id,
                        "username": user_data.username,
                        "similarity_score": similarity_score,
                        "total_runs": user_data.total_runs
                    })
            
            # Benzerlik skoruna göre sırala
            similar_users.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return similar_users[:5]  # En benzer 5 kullanıcı
            
        except Exception as e:
            logger.warning(f"Error finding similar users: {str(e)}")
            return []
    
    def _calculate_user_similarity(self, user_history: Dict[str, Any], 
                                 other_user: Any, target_success_rate: float, 
                                 target_active_days: int) -> float:
        """Kullanıcı benzerlik skoru hesapla"""
        # Basit benzerlik hesaplama (gerçek uygulamada daha karmaşık olabilir)
        total_runs_similarity = min(1.0, abs(user_history.get("total_runs", 0) - other_user.total_runs) / 10)
        activity_similarity = min(1.0, abs(target_active_days - 0) / 30)  # Placeholder
        
        # Ağırlıklı ortalama
        similarity = (total_runs_similarity * 0.6 + activity_similarity * 0.4)
        return max(0, 1 - similarity)
    
    async def _get_algorithm_performance_data(self, db: AsyncSession) -> Dict[str, Any]:
        """Algoritma performans verilerini getir"""
        try:
            # Tüm algoritma çalıştırmalarının istatistikleri
            result = await db.execute(
                select(
                    AlgorithmRun.algorithm_type,
                    func.count(AlgorithmRun.id).label('total_runs'),
                    func.avg(AlgorithmRun.execution_time).label('avg_execution_time'),
                    func.count(AlgorithmRun.id).filter(AlgorithmRun.status == 'completed').label('successful_runs')
                )
                .group_by(AlgorithmRun.algorithm_type)
            )
            performance_data = result.fetchall()
            
            algorithm_performance = {}
            for data in performance_data:
                algo_name = data.algorithm_type.value if data.algorithm_type else "unknown"
                algorithm_performance[algo_name] = {
                    "total_runs": data.total_runs,
                    "success_rate": data.successful_runs / data.total_runs if data.total_runs > 0 else 0,
                    "avg_execution_time": float(data.avg_execution_time) if data.avg_execution_time else 0
                }
            
            return algorithm_performance
            
        except Exception as e:
            logger.warning(f"Error getting algorithm performance data: {str(e)}")
            return {}
    
    async def _create_personalized_recommendation(self, user_history: Dict[str, Any],
                                                problem_analysis: Dict[str, Any],
                                                similar_users: List[Dict[str, Any]],
                                                algorithm_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Kişiselleştirilmiş öneri oluştur"""
        try:
            # Problem türüne göre algoritma öncelikleri
            problem_type = problem_analysis.get("problem_type", "medium")
            complexity = problem_analysis.get("complexity", 0.5)
            
            # Algoritma önerileri
            recommendations = []
            
            if problem_type == "small":
                # Küçük problemler için hızlı algoritmalar
                recommendations.extend([
                    {"algorithm": "greedy", "priority": 0.9, "reason": "Küçük problemler için hızlı ve etkili"},
                    {"algorithm": "cp_sat", "priority": 0.8, "reason": "Küçük problemler için optimal çözüm"},
                    {"algorithm": "simplex", "priority": 0.7, "reason": "Doğrusal programlama yaklaşımı"}
                ])
            elif problem_type == "medium":
                # Orta problemler için dengeli algoritmalar
                recommendations.extend([
                    {"algorithm": "cp_sat", "priority": 0.9, "reason": "Orta boyutlu problemler için ideal"},
                    {"algorithm": "nsga_ii", "priority": 0.8, "reason": "Çok amaçlı optimizasyon"},
                    {"algorithm": "simulated_annealing", "priority": 0.7, "reason": "Metaheuristik yaklaşım"}
                ])
            else:  # large
                # Büyük problemler için ölçeklenebilir algoritmalar
                recommendations.extend([
                    {"algorithm": "hybrid_cp_sat_nsga", "priority": 0.9, "reason": "Büyük problemler için hibrit yaklaşım"},
                    {"algorithm": "genetic_algorithm", "priority": 0.8, "reason": "Evrimsel optimizasyon"},
                    {"algorithm": "pso", "priority": 0.7, "reason": "Parçacık sürü optimizasyonu"}
                ])
            
            # Kullanıcı geçmişine göre ayarla
            most_used = user_history.get("most_used_algorithm", "none")
            if most_used != "none":
                # En çok kullanılan algoritmanın önceliğini artır
                for rec in recommendations:
                    if rec["algorithm"] == most_used:
                        rec["priority"] = min(1.0, rec["priority"] + 0.1)
                        rec["reason"] += " (Sık kullandığınız algoritma)"
            
            # Benzer kullanıcıların başarılı algoritmalarını dikkate al
            if similar_users:
                similar_algorithm_scores = {}
                for user in similar_users:
                    # Bu kısım gerçek veriye bağlı olarak implement edilmeli
                    similar_algorithm_scores["cp_sat"] = similar_algorithm_scores.get("cp_sat", 0) + 0.1
                
                for rec in recommendations:
                    algo_name = rec["algorithm"]
                    if algo_name in similar_algorithm_scores:
                        rec["priority"] = min(1.0, rec["priority"] + similar_algorithm_scores[algo_name])
                        rec["reason"] += " (Benzer kullanıcıların tercihi)"
            
            # Önceliğe göre sırala
            recommendations.sort(key=lambda x: x["priority"], reverse=True)
            
            # En iyi öneri
            best_recommendation = recommendations[0] if recommendations else {"algorithm": "greedy", "priority": 0.5}
            
            # Güven skoru hesapla
            confidence = min(0.95, best_recommendation["priority"] + 
                           (user_history.get("success_rate", 0.5) * 0.3))
            
            return {
                "recommended_algorithm": best_recommendation["algorithm"],
                "confidence": confidence,
                "reasoning": best_recommendation["reason"],
                "all_recommendations": recommendations,
                "problem_analysis": problem_analysis,
                "user_history_impact": {
                    "most_used_algorithm": most_used,
                    "success_rate": user_history.get("success_rate", 0),
                    "total_runs": user_history.get("total_runs", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating personalized recommendation: {str(e)}")
            return {
                "recommended_algorithm": "greedy",
                "confidence": 0.5,
                "reasoning": "Varsayılan öneri (hata durumu)",
                "all_recommendations": [],
                "problem_analysis": problem_analysis,
                "user_history_impact": {}
            }
    
    async def _cache_recommendation(self, user_id: int, problem_data: Dict[str, Any], 
                                  recommendation: Dict[str, Any]) -> None:
        """Öneriyi cache'le"""
        try:
            cache_key = f"user_recommendation_{user_id}_{hash(str(problem_data))}"
            await self.cache_service.cache_user_recommendation(
                cache_key, recommendation, ttl=3600  # 1 saat
            )
        except Exception as e:
            logger.warning(f"Error caching recommendation: {str(e)}")
    
    async def _record_user_behavior(self, user_id: int, problem_data: Dict[str, Any], 
                                  recommendation: Dict[str, Any], db: AsyncSession) -> None:
        """Kullanıcı davranışını kaydet"""
        try:
            # Bu kısım gerçek uygulamada user_behavior tablosuna kayıt yapabilir
            logger.info(f"Recording user behavior for user {user_id}: {recommendation['recommended_algorithm']}")
        except Exception as e:
            logger.warning(f"Error recording user behavior: {str(e)}")
    
    async def _get_algorithm_usage_history(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Algoritma kullanım geçmişini getir"""
        try:
            result = await db.execute(
                select(
                    AlgorithmRun.algorithm_type,
                    func.count(AlgorithmRun.id).label('usage_count'),
                    func.avg(AlgorithmRun.execution_time).label('avg_time'),
                    func.max(AlgorithmRun.created_at).label('last_used')
                )
                .filter(AlgorithmRun.user_id == user_id)
                .group_by(AlgorithmRun.algorithm_type)
                .order_by(desc(func.count(AlgorithmRun.id)))
            )
            
            usage_history = []
            for data in result.fetchall():
                usage_history.append({
                    "algorithm": data.algorithm_type.value if data.algorithm_type else "unknown",
                    "usage_count": data.usage_count,
                    "avg_execution_time": float(data.avg_time) if data.avg_time else 0,
                    "last_used": data.last_used.isoformat() if data.last_used else None
                })
            
            return {
                "usage_history": usage_history,
                "total_algorithms_used": len(usage_history),
                "most_used_algorithm": usage_history[0]["algorithm"] if usage_history else "none"
            }
            
        except Exception as e:
            logger.warning(f"Error getting algorithm usage history: {str(e)}")
            return {"usage_history": [], "total_algorithms_used": 0, "most_used_algorithm": "none"}
    
    async def _calculate_success_rates(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Başarı oranlarını hesapla"""
        try:
            result = await db.execute(
                select(
                    AlgorithmRun.algorithm_type,
                    func.count(AlgorithmRun.id).label('total_runs'),
                    func.count(AlgorithmRun.id).filter(AlgorithmRun.status == 'completed').label('successful_runs')
                )
                .filter(AlgorithmRun.user_id == user_id)
                .group_by(AlgorithmRun.algorithm_type)
            )
            
            success_rates = {}
            total_runs = 0
            total_successful = 0
            
            for data in result.fetchall():
                algo_name = data.algorithm_type.value if data.algorithm_type else "unknown"
                success_rate = data.successful_runs / data.total_runs if data.total_runs > 0 else 0
                success_rates[algo_name] = {
                    "success_rate": success_rate,
                    "total_runs": data.total_runs,
                    "successful_runs": data.successful_runs
                }
                total_runs += data.total_runs
                total_successful += data.successful_runs
            
            overall_success_rate = total_successful / total_runs if total_runs > 0 else 0
            
            return {
                "by_algorithm": success_rates,
                "overall_success_rate": overall_success_rate,
                "total_runs": total_runs,
                "total_successful": total_successful
            }
            
        except Exception as e:
            logger.warning(f"Error calculating success rates: {str(e)}")
            return {"by_algorithm": {}, "overall_success_rate": 0, "total_runs": 0, "total_successful": 0}
    
    async def _get_best_performing_problems(self, user_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """En iyi performans gösterdiği problem türlerini getir"""
        try:
            # En başarılı çalıştırmaları getir
            result = await db.execute(
                select(AlgorithmRun)
                .filter(
                    and_(
                        AlgorithmRun.user_id == user_id,
                        AlgorithmRun.status == 'completed'
                    )
                )
                .order_by(desc(AlgorithmRun.score))
                .limit(10)
            )
            
            best_runs = result.scalars().all()
            
            best_performing_problems = []
            for run in best_runs:
                best_performing_problems.append({
                    "algorithm": run.algorithm_type.value if run.algorithm_type else "unknown",
                    "score": run.score,
                    "execution_time": float(run.execution_time) if run.execution_time else 0,
                    "date": run.created_at.isoformat(),
                    "parameters": run.parameters
                })
            
            return best_performing_problems
            
        except Exception as e:
            logger.warning(f"Error getting best performing problems: {str(e)}")
            return []
    
    async def _generate_improvement_suggestions(self, algorithm_usage: Dict[str, Any],
                                              success_rates: Dict[str, Any],
                                              best_performing_problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """İyileştirme önerileri oluştur"""
        suggestions = []
        
        # Genel başarı oranı düşükse
        overall_success_rate = success_rates.get("overall_success_rate", 0)
        if overall_success_rate < 0.7:
            suggestions.append({
                "category": "Başarı Oranı",
                "priority": "High",
                "suggestion": "Algoritma parametrelerini optimize edin",
                "reason": f"Mevcut başarı oranınız %{overall_success_rate*100:.1f}"
            })
        
        # Çeşitlilik eksikliği
        total_algorithms = algorithm_usage.get("total_algorithms_used", 0)
        if total_algorithms < 3:
            suggestions.append({
                "category": "Algoritma Çeşitliliği",
                "priority": "Medium",
                "suggestion": "Farklı algoritma türlerini deneyin",
                "reason": f"Sadece {total_algorithms} farklı algoritma kullandınız"
            })
        
        # En iyi performans analizi
        if best_performing_problems:
            best_algorithm = best_performing_problems[0]["algorithm"]
            suggestions.append({
                "category": "Optimizasyon",
                "priority": "Medium",
                "suggestion": f"{best_algorithm} algoritmasını daha sık kullanın",
                "reason": "Bu algoritma ile en yüksek skorları aldınız"
            })
        
        return suggestions
    
    async def _get_comparative_analysis(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Karşılaştırmalı analiz getir"""
        try:
            # Tüm kullanıcıların ortalama performansı
            result = await db.execute(
                select(
                    func.avg(AlgorithmRun.score).label('avg_score'),
                    func.avg(AlgorithmRun.execution_time).label('avg_time'),
                    func.count(AlgorithmRun.id).label('total_runs')
                )
                .filter(AlgorithmRun.status == 'completed')
            )
            
            global_stats = result.fetchone()
            
            # Kullanıcının ortalama performansı
            user_result = await db.execute(
                select(
                    func.avg(AlgorithmRun.score).label('avg_score'),
                    func.avg(AlgorithmRun.execution_time).label('avg_time'),
                    func.count(AlgorithmRun.id).label('total_runs')
                )
                .filter(
                    and_(
                        AlgorithmRun.user_id == user_id,
                        AlgorithmRun.status == 'completed'
                    )
                )
            )
            
            user_stats = user_result.fetchone()
            
            return {
                "user_performance": {
                    "avg_score": float(user_stats.avg_score) if user_stats.avg_score else 0,
                    "avg_time": float(user_stats.avg_time) if user_stats.avg_time else 0,
                    "total_runs": user_stats.total_runs or 0
                },
                "global_average": {
                    "avg_score": float(global_stats.avg_score) if global_stats.avg_score else 0,
                    "avg_time": float(global_stats.avg_time) if global_stats.avg_time else 0,
                    "total_runs": global_stats.total_runs or 0
                },
                "performance_vs_global": {
                    "score_comparison": "above" if (user_stats.avg_score or 0) > (global_stats.avg_score or 0) else "below",
                    "time_comparison": "faster" if (user_stats.avg_time or 0) < (global_stats.avg_time or 0) else "slower"
                }
            }
            
        except Exception as e:
            logger.warning(f"Error getting comparative analysis: {str(e)}")
            return {"user_performance": {}, "global_average": {}, "performance_vs_global": {}}
    
    async def _analyze_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Kullanıcı tercihlerini analiz et"""
        # Bu kısım gerçek uygulamada user_preferences tablosundan veri çekebilir
        return {
            "preferred_algorithms": ["cp_sat", "nsga_ii"],
            "preferred_parameters": {
                "max_iterations": 100,
                "timeout": 30
            },
            "success_threshold": 0.8
        }
    
    async def _calculate_optimal_parameters(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimal parametreleri hesapla"""
        problem_size = len(problem_data.get("projects", []))
        
        # Problem boyutuna göre parametreler
        if problem_size < 20:
            return {
                "max_iterations": 50,
                "timeout": 15,
                "population_size": 20
            }
        elif problem_size < 50:
            return {
                "max_iterations": 100,
                "timeout": 30,
                "population_size": 50
            }
        else:
            return {
                "max_iterations": 200,
                "timeout": 60,
                "population_size": 100
            }
    
    async def _merge_preferences_and_optimal(self, user_preferences: Dict[str, Any], 
                                           optimal_params: Dict[str, Any]) -> Dict[str, Any]:
        """Tercihler ve optimal parametreleri birleştir"""
        merged = optimal_params.copy()
        
        # Kullanıcı tercihlerini öncelikle
        preferred_params = user_preferences.get("preferred_parameters", {})
        for key, value in preferred_params.items():
            if key in merged:
                # Kullanıcı tercihi ile optimal değerin ortalaması
                merged[key] = int((merged[key] + value) / 2)
        
        return merged
