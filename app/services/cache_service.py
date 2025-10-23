"""
Cache service for performance optimization
Proje açıklamasına göre: Performans optimizasyonu implementasyonu
"""

import json
import pickle
import hashlib
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
import asyncio
import logging

from app.core.cache import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """Cache service for performance optimization"""
    
    def __init__(self):
        self.redis_client = None
        self.cache_prefix = "optimization_planner"
        self.default_ttl = 3600  # 1 hour
        self.algorithm_cache_ttl = 1800  # 30 minutes for algorithm results
        self.user_cache_ttl = 900  # 15 minutes for user-specific data
    
    async def _get_redis(self):
        """Get Redis client with lazy initialization"""
        if self.redis_client is None:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_parts = [self.cache_prefix, prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest())
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (dict, list)):
                key_parts.append(f"{key}:{hashlib.md5(json.dumps(value, sort_keys=True).encode()).hexdigest()}")
            else:
                key_parts.append(f"{key}:{value}")
        
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return None
            
            value = await redis.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then as pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    return value.decode() if isinstance(value, bytes) else value
        
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, default=str)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = pickle.dumps(value)
            
            ttl = ttl or self.default_ttl
            await redis.setex(key, ttl, serialized_value)
            return True
        
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            result = await redis.delete(key)
            return result > 0
        
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return False
            
            result = await redis.exists(key)
            return result > 0
        
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return 0
            
            keys = await redis.keys(f"{self.cache_prefix}:{pattern}")
            if keys:
                return await redis.delete(*keys)
            return 0
        
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern {pattern}: {e}")
            return 0
    
    # Algorithm-specific caching methods
    
    async def cache_algorithm_result(self, algorithm_name: str, params: Dict[str, Any], result: Any) -> bool:
        """Cache algorithm result"""
        key = self._generate_cache_key("algorithm_result", algorithm_name, **params)
        return await self.set(key, result, self.algorithm_cache_ttl)
    
    async def get_cached_algorithm_result(self, algorithm_name: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached algorithm result"""
        key = self._generate_cache_key("algorithm_result", algorithm_name, **params)
        return await self.get(key)
    
    async def cache_problem_analysis(self, problem_data: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Cache problem analysis"""
        key = self._generate_cache_key("problem_analysis", **problem_data)
        return await self.set(key, analysis, self.default_ttl)
    
    async def get_cached_problem_analysis(self, problem_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached problem analysis"""
        key = self._generate_cache_key("problem_analysis", **problem_data)
        return await self.get(key)
    
    async def cache_algorithm_recommendation(self, user_id: int, problem_data: Dict[str, Any], recommendation: Dict[str, Any]) -> bool:
        """Cache algorithm recommendation"""
        key = self._generate_cache_key("algorithm_recommendation", user_id, **problem_data)
        return await self.set(key, recommendation, self.user_cache_ttl)
    
    async def get_cached_algorithm_recommendation(self, user_id: int, problem_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached algorithm recommendation"""
        key = self._generate_cache_key("algorithm_recommendation", user_id, **problem_data)
        return await self.get(key)
    
    async def cache_objective_scores(self, problem_data: Dict[str, Any], scores: Dict[str, Any]) -> bool:
        """Cache objective scores"""
        key = self._generate_cache_key("objective_scores", **problem_data)
        return await self.set(key, scores, self.default_ttl)
    
    async def get_cached_objective_scores(self, problem_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached objective scores"""
        key = self._generate_cache_key("objective_scores", **problem_data)
        return await self.get(key)
    
    async def cache_weighted_score(self, objective_scores: Dict[str, float], weights: Dict[str, float], result: Dict[str, Any]) -> bool:
        """Cache weighted score calculation"""
        key = self._generate_cache_key("weighted_score", objective_scores, weights)
        return await self.set(key, result, self.default_ttl)
    
    async def get_cached_weighted_score(self, objective_scores: Dict[str, float], weights: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Get cached weighted score calculation"""
        key = self._generate_cache_key("weighted_score", objective_scores, weights)
        return await self.get(key)
    
    # User-specific caching methods
    
    async def cache_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Cache user preferences"""
        key = self._generate_cache_key("user_preferences", user_id)
        return await self.set(key, preferences, self.user_cache_ttl)
    
    async def get_cached_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user preferences"""
        key = self._generate_cache_key("user_preferences", user_id)
        return await self.get(key)
    
    async def cache_user_history(self, user_id: int, history: Dict[str, Any]) -> bool:
        """Cache user history"""
        key = self._generate_cache_key("user_history", user_id)
        return await self.set(key, history, self.user_cache_ttl)
    
    async def get_cached_user_history(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user history"""
        key = self._generate_cache_key("user_history", user_id)
        return await self.get(key)
    
    # System-wide caching methods
    
    async def cache_system_config(self, config: Dict[str, Any]) -> bool:
        """Cache system configuration"""
        key = self._generate_cache_key("system_config")
        return await self.set(key, config, self.default_ttl)
    
    async def get_cached_system_config(self) -> Optional[Dict[str, Any]]:
        """Get cached system configuration"""
        key = self._generate_cache_key("system_config")
        return await self.get(key)
    
    async def cache_algorithm_list(self, algorithms: List[Dict[str, Any]]) -> bool:
        """Cache algorithm list"""
        key = self._generate_cache_key("algorithm_list")
        return await self.set(key, algorithms, self.default_ttl)
    
    async def get_cached_algorithm_list(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached algorithm list"""
        key = self._generate_cache_key("algorithm_list")
        return await self.get(key)
    
    # Cache invalidation methods
    
    async def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cache entries for a user"""
        patterns = [
            f"user_preferences:{user_id}",
            f"user_history:{user_id}",
            f"algorithm_recommendation:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.clear_pattern(pattern)
            total_deleted += deleted
        
        return total_deleted
    
    async def invalidate_algorithm_cache(self, algorithm_name: Optional[str] = None) -> int:
        """Invalidate algorithm-related cache entries"""
        if algorithm_name:
            pattern = f"algorithm_result:{algorithm_name}:*"
        else:
            pattern = "algorithm_result:*"
        
        return await self.clear_pattern(pattern)
    
    async def invalidate_problem_cache(self) -> int:
        """Invalidate problem-related cache entries"""
        patterns = [
            "problem_analysis:*",
            "objective_scores:*",
            "weighted_score:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.clear_pattern(pattern)
            total_deleted += deleted
        
        return total_deleted
    
    async def invalidate_all_cache(self) -> int:
        """Invalidate all cache entries"""
        return await self.clear_pattern("*")
    
    # Cache statistics and monitoring
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis = await self._get_redis()
            if redis is None:
                return {"error": "Redis not available"}
            
            info = await redis.info()
            keys = await redis.keys(f"{self.cache_prefix}:*")
            
            return {
                "total_keys": len(keys),
                "memory_usage": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "cache_prefix": self.cache_prefix,
                "patterns": {
                    "algorithm_results": len([k for k in keys if b"algorithm_result" in k]),
                    "problem_analysis": len([k for k in keys if b"problem_analysis" in k]),
                    "user_data": len([k for k in keys if b"user_" in k]),
                    "system_config": len([k for k in keys if b"system_config" in k])
                }
            }
        
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}


# Global cache service instance
cache_service = CacheService()
