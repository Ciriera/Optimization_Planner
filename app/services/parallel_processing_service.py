"""
Parallel processing service for performance optimization
Proje açıklamasına göre: Parallel processing ve caching mekanizmaları
"""

import asyncio
import concurrent.futures
from typing import Any, Dict, List, Optional, Callable, Union
from functools import partial
import multiprocessing as mp
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class ParallelProcessingService:
    """Service for parallel processing optimization"""
    
    def __init__(self):
        self.max_workers = min(settings.MAX_WORKERS, mp.cpu_count())
        self.thread_pool_executor = None
        self.process_pool_executor = None
        
    def _get_thread_pool(self):
        """Get or create thread pool executor"""
        if self.thread_pool_executor is None:
            self.thread_pool_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="optimization_thread"
            )
        return self.thread_pool_executor
    
    def _get_process_pool(self):
        """Get or create process pool executor"""
        if self.process_pool_executor is None:
            self.process_pool_executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=self.max_workers
            )
        return self.process_pool_executor
    
    async def run_parallel_async(self, tasks: List[Callable], max_concurrency: Optional[int] = None) -> List[Any]:
        """
        Run multiple async tasks in parallel with controlled concurrency.
        
        Args:
            tasks: List of async callable tasks
            max_concurrency: Maximum number of concurrent tasks
            
        Returns:
            List of results from tasks
        """
        if not tasks:
            return []
        
        max_concurrency = max_concurrency or self.max_workers
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def run_with_semaphore(task):
            async with semaphore:
                if asyncio.iscoroutinefunction(task):
                    return await task()
                else:
                    return task()
        
        try:
            results = await asyncio.gather(*[run_with_semaphore(task) for task in tasks])
            return results
        except Exception as e:
            logger.error(f"Error in parallel async execution: {e}")
            raise
    
    async def run_parallel_sync(self, tasks: List[Callable], executor_type: str = "thread") -> List[Any]:
        """
        Run multiple synchronous tasks in parallel using thread or process pool.
        
        Args:
            tasks: List of synchronous callable tasks
            executor_type: "thread" or "process"
            
        Returns:
            List of results from tasks
        """
        if not tasks:
            return []
        
        try:
            if executor_type == "thread":
                executor = self._get_thread_pool()
            elif executor_type == "process":
                executor = self._get_process_pool()
            else:
                raise ValueError(f"Invalid executor_type: {executor_type}")
            
            loop = asyncio.get_event_loop()
            
            # Submit all tasks
            futures = [loop.run_in_executor(executor, task) for task in tasks]
            
            # Wait for all to complete
            results = await asyncio.gather(*futures)
            return results
            
        except Exception as e:
            logger.error(f"Error in parallel sync execution: {e}")
            raise
    
    async def run_algorithm_parallel(self, algorithm_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run multiple algorithm configurations in parallel.
        
        Args:
            algorithm_configs: List of algorithm configuration dictionaries
            
        Returns:
            List of algorithm results
        """
        async def run_algorithm(config):
            try:
                from app.services.algorithm import AlgorithmService
                algorithm_service = AlgorithmService()
                
                # Run algorithm with configuration
                result = await algorithm_service.run_algorithm(
                    algorithm_type=config["algorithm_type"],
                    parameters=config.get("parameters", {}),
                    timeout=config.get("timeout", 300)
                )
                
                return {
                    "config": config,
                    "result": result,
                    "success": True,
                    "execution_time": result.get("execution_time", 0)
                }
                
            except Exception as e:
                logger.error(f"Algorithm execution failed for config {config}: {e}")
                return {
                    "config": config,
                    "result": None,
                    "success": False,
                    "error": str(e),
                    "execution_time": 0
                }
        
        # Run algorithms in parallel with limited concurrency
        max_concurrency = min(len(algorithm_configs), self.max_workers)
        results = await self.run_parallel_async([partial(run_algorithm, config) for config in algorithm_configs], max_concurrency)
        
        return results
    
    async def run_objective_calculation_parallel(self, problem_data: Dict[str, Any], schedules: List[Any]) -> Dict[str, float]:
        """
        Run objective function calculations in parallel.
        
        Args:
            problem_data: Problem data dictionary
            schedules: List of schedule objects
            
        Returns:
            Dictionary of objective scores
        """
        from app.services.scoring import ScoringService
        
        async def calculate_load_balance():
            scoring_service = ScoringService()
            return await scoring_service._calculate_load_balance_score(problem_data.get("db"), schedules)
        
        async def calculate_classroom_changes():
            scoring_service = ScoringService()
            return scoring_service._calculate_classroom_changes_score(schedules)
        
        async def calculate_time_efficiency():
            scoring_service = ScoringService()
            return scoring_service._calculate_time_efficiency_score(schedules)
        
        async def calculate_session_minimization():
            scoring_service = ScoringService()
            return scoring_service._calculate_session_minimization_score(schedules)
        
        async def calculate_rule_compliance():
            scoring_service = ScoringService()
            return await scoring_service._calculate_rule_compliance_score(problem_data.get("db"), schedules)
        
        # Run all objective calculations in parallel
        tasks = [
            calculate_load_balance,
            calculate_classroom_changes,
            calculate_time_efficiency,
            calculate_session_minimization,
            calculate_rule_compliance
        ]
        
        results = await self.run_parallel_async(tasks)
        
        return {
            "load_balance": results[0],
            "classroom_changes": results[1],
            "time_efficiency": results[2],
            "session_minimization": results[3],
            "rule_compliance": results[4]
        }
    
    async def run_problem_analysis_parallel(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run problem analysis components in parallel.
        
        Args:
            problem_data: Problem data dictionary
            
        Returns:
            Analysis results dictionary
        """
        def analyze_complexity():
            from app.services.recommendation_service import RecommendationService
            service = RecommendationService(None)  # No DB needed for this analysis
            return service._calculate_complexity_score(
                problem_data.get("projects", []),
                problem_data.get("instructors", []),
                problem_data.get("classrooms", []),
                problem_data.get("timeslots", [])
            )
        
        def analyze_constraints():
            from app.services.recommendation_service import RecommendationService
            service = RecommendationService(None)
            return service._has_strict_constraints(problem_data.get("projects", []))
        
        def analyze_multi_objective():
            from app.services.recommendation_service import RecommendationService
            service = RecommendationService(None)
            return service._requires_multi_objective_optimization(
                problem_data.get("projects", []),
                problem_data.get("instructors", [])
            )
        
        def count_project_types():
            projects = problem_data.get("projects", [])
            bitirme_count = len([p for p in projects if p.get("type") == "bitirme"])
            ara_count = len([p for p in projects if p.get("type") == "ara"])
            return {"bitirme_count": bitirme_count, "ara_count": ara_count}
        
        # Run analysis components in parallel
        tasks = [analyze_complexity, analyze_constraints, analyze_multi_objective, count_project_types]
        results = await self.run_parallel_sync(tasks, "thread")
        
        complexity_score, has_strict_constraints, requires_multi_objective, project_counts = results
        
        return {
            "complexity_score": complexity_score,
            "has_strict_constraints": has_strict_constraints,
            "requires_multi_objective": requires_multi_objective,
            "bitirme_project_count": project_counts["bitirme_count"],
            "ara_project_count": project_counts["ara_count"],
            "project_count": len(problem_data.get("projects", [])),
            "instructor_count": len(problem_data.get("instructors", [])),
            "classroom_count": len(problem_data.get("classrooms", [])),
            "timeslot_count": len(problem_data.get("timeslots", []))
        }
    
    async def run_validation_parallel(self, validation_tasks: List[Callable]) -> List[Dict[str, Any]]:
        """
        Run validation tasks in parallel.
        
        Args:
            validation_tasks: List of validation callable tasks
            
        Returns:
            List of validation results
        """
        async def run_validation(task):
            try:
                if asyncio.iscoroutinefunction(task):
                    result = await task()
                else:
                    result = task()
                
                return {
                    "success": True,
                    "result": result,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Validation task failed: {e}")
                return {
                    "success": False,
                    "result": None,
                    "error": str(e)
                }
        
        results = await self.run_parallel_async([partial(run_validation, task) for task in validation_tasks])
        return results
    
    async def run_data_processing_parallel(self, data_chunks: List[List[Any]], processing_func: Callable) -> List[Any]:
        """
        Process data chunks in parallel.
        
        Args:
            data_chunks: List of data chunks to process
            processing_func: Function to process each chunk
            
        Returns:
            List of processed results
        """
        async def process_chunk(chunk):
            try:
                if asyncio.iscoroutinefunction(processing_func):
                    return await processing_func(chunk)
                else:
                    return processing_func(chunk)
            except Exception as e:
                logger.error(f"Data processing failed for chunk: {e}")
                return None
        
        # Process chunks in parallel
        results = await self.run_parallel_async([partial(process_chunk, chunk) for chunk in data_chunks])
        
        # Filter out None results
        return [result for result in results if result is not None]
    
    def cleanup(self):
        """Cleanup resources"""
        if self.thread_pool_executor:
            self.thread_pool_executor.shutdown(wait=True)
            self.thread_pool_executor = None
        
        if self.process_pool_executor:
            self.process_pool_executor.shutdown(wait=True)
            self.process_pool_executor = None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "max_workers": self.max_workers,
            "cpu_count": mp.cpu_count(),
            "thread_pool_active": self.thread_pool_executor is not None,
            "process_pool_active": self.process_pool_executor is not None,
            "timestamp": datetime.now().isoformat()
        }


# Global parallel processing service instance
parallel_processing_service = ParallelProcessingService()
