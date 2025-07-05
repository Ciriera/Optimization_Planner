from typing import Dict, Any, List, Optional
from celery import shared_task
from sqlalchemy.orm import Session
import json
from datetime import datetime

from app import crud, models, schemas
from app.db.session import SessionLocal
from app.algorithms.factory import get_algorithm
from app.services.algorithm import calculate_algorithm_score
from app.algorithms.simulated_annealing import SimulatedAnnealing
from app.core.cache import redis_client


@shared_task(bind=True, name="app.tasks.algorithms.run_algorithm")
def run_algorithm(
    self,
    algorithm_name: str,
    params: Dict[str, Any],
    user_id: int,
) -> Dict[str, Any]:
    """
    Seçilen algoritmayı arka planda çalıştırır.
    
    Args:
        algorithm_name: Algoritma adı
        params: Algoritma parametreleri
        user_id: Kullanıcı ID
        
    Returns:
        Algoritma sonuçları
    """
    db = SessionLocal()
    try:
        # Algoritmayı al
        algorithm = get_algorithm(algorithm_name)
        
        # Algoritmayı çalıştır
        start_time = datetime.utcnow()
        result = algorithm.run(db, **params)
        end_time = datetime.utcnow()
        
        # Çalışma süresini hesapla
        execution_time = (end_time - start_time).total_seconds()
        
        # Algoritma başarı skorunu hesapla
        score = calculate_algorithm_score(db, result)
        
        # Algoritma çalıştırma kaydını oluştur
        algorithm_run = crud.algorithm.create_run(
            db,
            obj_in=schemas.AlgorithmRunCreate(
                algorithm=algorithm_name,
                params=params,
                score=score,
                execution_time=execution_time,
                result=result,
                user_id=user_id
            )
        )
        
        # Sonucu döndür
        return {
            "status": "success",
            "algorithm_run_id": algorithm_run.id,
            "algorithm": algorithm_name,
            "score": score,
            "execution_time": execution_time,
            "result": result
        }
    finally:
        db.close()


@shared_task(bind=True, name="app.tasks.algorithms.compare_algorithms")
def compare_algorithms(
    self,
    algorithm_names: List[str],
    params: Dict[str, Any],
    user_id: int,
) -> Dict[str, Any]:
    """
    Birden fazla algoritmayı karşılaştırır.
    
    Args:
        algorithm_names: Algoritma adları
        params: Algoritma parametreleri
        user_id: Kullanıcı ID
        
    Returns:
        Algoritma karşılaştırma sonuçları
    """
    db = SessionLocal()
    try:
        results = []
        
        for algorithm_name in algorithm_names:
            # Algoritmayı al
            algorithm = get_algorithm(algorithm_name)
            
            # Algoritmayı çalıştır
            start_time = datetime.utcnow()
            result = algorithm.run(db, **params)
            end_time = datetime.utcnow()
            
            # Çalışma süresini hesapla
            execution_time = (end_time - start_time).total_seconds()
            
            # Algoritma başarı skorunu hesapla
            score = calculate_algorithm_score(db, result)
            
            # Algoritma çalıştırma kaydını oluştur
            algorithm_run = crud.algorithm.create_run(
                db,
                obj_in=schemas.AlgorithmRunCreate(
                    algorithm=algorithm_name,
                    params=params,
                    score=score,
                    execution_time=execution_time,
                    result=result,
                    user_id=user_id
                )
            )
            
            # Sonucu ekle
            results.append({
                "algorithm_run_id": algorithm_run.id,
                "algorithm": algorithm_name,
                "score": score,
                "execution_time": execution_time
            })
        
        # Sonuçları skora göre sırala
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # En iyi algoritmayı belirle
        best_algorithm = results[0]["algorithm"] if results else None
        
        return {
            "status": "success",
            "best_algorithm": best_algorithm,
            "results": results
        }
    finally:
        db.close()


@shared_task(name="run_simulated_annealing")
def run_simulated_annealing(
    project_type: str = "ALL",
    is_makeup: bool = False,
    initial_temperature: float = 1000.0,
    cooling_rate: float = 0.95,
    iterations: int = 1000,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the simulated annealing algorithm as a background task.
    
    Args:
        project_type: Type of projects to schedule (FINAL, INTERIM, ALL)
        is_makeup: Whether this is for makeup exams
        initial_temperature: Initial temperature for simulated annealing
        cooling_rate: Cooling rate for simulated annealing
        iterations: Number of iterations
        task_id: Optional task ID for caching results
        
    Returns:
        The algorithm results
    """
    # Create database session
    db = SessionLocal()
    
    try:
        # Create algorithm instance
        algorithm = SimulatedAnnealing([], [], [])
        
        # Run the algorithm
        result = algorithm.run(
            db=db,
            project_type=project_type,
            is_makeup=is_makeup,
            initial_temperature=initial_temperature,
            cooling_rate=cooling_rate,
            iterations=iterations
        )
        
        # Cache the result if task_id is provided
        if task_id and redis_client:
            redis_client.set(
                f"algorithm_result:{task_id}",
                json.dumps(result),
                ex=86400  # 24 hours expiration
            )
        
        return result
    finally:
        db.close()


@shared_task(name="compare_algorithms")
def compare_algorithms(
    algorithms: List[Dict[str, Any]],
    project_type: str = "ALL",
    is_makeup: bool = False,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run multiple algorithms with different parameters and compare their results.
    
    Args:
        algorithms: List of algorithm configurations to run
        project_type: Type of projects to schedule
        is_makeup: Whether this is for makeup exams
        task_id: Optional task ID for caching results
        
    Returns:
        Comparison results
    """
    # Create database session
    db = SessionLocal()
    
    try:
        results = []
        
        for algo_config in algorithms:
            algorithm_name = algo_config.get("name")
            parameters = algo_config.get("parameters", {})
            
            if algorithm_name == "simulated_annealing":
                # Create algorithm instance
                algorithm = SimulatedAnnealing([], [], [])
                
                # Run the algorithm
                result = algorithm.run(
                    db=db,
                    project_type=project_type,
                    is_makeup=is_makeup,
                    **parameters
                )
                
                results.append({
                    "algorithm": algorithm_name,
                    "parameters": parameters,
                    "result": result
                })
        
        # Prepare comparison metrics
        comparison = {
            "project_type": project_type,
            "is_makeup": is_makeup,
            "results": results,
            "best_algorithm": None,
            "metrics": {}
        }
        
        # Find the best algorithm based on final energy
        if results:
            best_algo = min(results, key=lambda x: x["result"].get("statistics", {}).get("final_energy", float('inf')))
            comparison["best_algorithm"] = {
                "name": best_algo["algorithm"],
                "parameters": best_algo["parameters"]
            }
            
            # Calculate metrics for comparison
            energies = [r["result"].get("statistics", {}).get("final_energy", float('inf')) for r in results]
            comparison["metrics"] = {
                "min_energy": min(energies),
                "max_energy": max(energies),
                "avg_energy": sum(energies) / len(energies)
            }
        
        # Cache the comparison if task_id is provided
        if task_id and redis_client:
            redis_client.set(
                f"algorithm_comparison:{task_id}",
                json.dumps(comparison),
                ex=86400  # 24 hours expiration
            )
        
        return comparison
    finally:
        db.close()


@shared_task(name="get_algorithm_result")
def get_algorithm_result(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cached algorithm result.
    
    Args:
        task_id: Task ID for retrieving cached results
        
    Returns:
        The cached result or None if not found
    """
    if redis_client:
        cached_result = redis_client.get(f"algorithm_result:{task_id}")
        if cached_result:
            return json.loads(cached_result)
    return None


@shared_task(name="get_algorithm_comparison")
def get_algorithm_comparison(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get cached algorithm comparison.
    
    Args:
        task_id: Task ID for retrieving cached comparison
        
    Returns:
        The cached comparison or None if not found
    """
    if redis_client:
        cached_comparison = redis_client.get(f"algorithm_comparison:{task_id}")
        if cached_comparison:
            return json.loads(cached_comparison)
    return None 