import redis
import aioredis
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import timedelta
from redis.exceptions import RedisError

from app.core.config import settings

# Logging
logger = logging.getLogger(__name__)

# Redis client for synchronous operations
redis_client = None

# Redis pool for asynchronous operations
redis_pool = None


async def init_redis_pool():
    """
    Initialize Redis connection pool for async operations.
    """
    global redis_pool, redis_client
    
    try:
        # Construct Redis URL if not explicitly set
        redis_url = settings.REDIS_URL
        
        # Create async Redis pool
        redis_pool = await aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Create sync Redis client
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # Test connection
        redis_client.ping()
        logger.info(f"Redis bağlantı havuzu başlatıldı: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        return True
    except RedisError as e:
        logger.warning(f"Redis bağlantısı kurulamadı: {e}")
        # Create mock Redis client
        redis_client = MockRedis()
        redis_pool = MockRedisPool()
        return False


def set_cache(key: str, value: Any, expire: Optional[int] = None) -> None:
    """
    Store data in Redis cache.
    
    Args:
        key: Cache key
        value: Value to store
        expire: Expiration time in seconds
    """
    if not redis_client:
        return
        
    try:
        # Serialize as JSON
        serialized_value = json.dumps(value)
        
        # Store in Redis
        redis_client.set(key, serialized_value)
        
        # Set TTL if specified
        if expire:
            redis_client.expire(key, expire)
    except Exception as e:
        # Catch Redis errors but don't block application
        logger.error(f"Redis cache error: {str(e)}")


def get_cache(key: str) -> Optional[Any]:
    """
    Retrieve data from Redis cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    if not redis_client:
        return None
        
    try:
        # Get data from Redis
        value = redis_client.get(key)
        
        # Deserialize JSON if data exists
        if value:
            return json.loads(value)
        
        return None
    except Exception as e:
        # Catch Redis errors but don't block application
        logger.error(f"Redis cache error: {str(e)}")
        return None


def delete_cache(key: str) -> None:
    """
    Delete data from Redis cache.
    
    Args:
        key: Cache key
    """
    if not redis_client:
        return
        
    try:
        redis_client.delete(key)
    except Exception as e:
        # Catch Redis errors but don't block application
        logger.error(f"Redis cache error: {str(e)}")


def clear_cache_pattern(pattern: str) -> None:
    """
    Delete all cache keys matching a pattern.
    
    Args:
        pattern: Key pattern (e.g., "user:*")
    """
    if not redis_client:
        return
        
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        # Catch Redis errors but don't block application
        logger.error(f"Redis cache error: {str(e)}")


async def set_cache_async(key: str, value: Any, expire: Optional[int] = None) -> None:
    """
    Store data in Redis cache asynchronously.
    
    Args:
        key: Cache key
        value: Value to store
        expire: Expiration time in seconds
    """
    if not redis_pool:
        return
        
    try:
        # Serialize as JSON
        serialized_value = json.dumps(value)
        
        # Store in Redis
        await redis_pool.set(key, serialized_value)
        
        # Set TTL if specified
        if expire:
            await redis_pool.expire(key, expire)
    except Exception as e:
        # Catch Redis errors but don't block application
        logger.error(f"Redis cache error: {str(e)}")


async def get_cache_async(key: str) -> Optional[Any]:
    """
    Retrieve data from Redis cache asynchronously.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None
    """
    if not redis_pool:
        return None
        
    try:
        # Get data from Redis
        value = await redis_pool.get(key)
        
        # Deserialize JSON if data exists
        if value:
            return json.loads(value)
        
        return None
    except Exception as e:
        # Catch Redis errors but don't block application
        logger.error(f"Redis cache error: {str(e)}")
        return None


def get_cache_key(*args: Any) -> str:
    """Generate a cache key from arguments"""
    return ":".join(str(arg) for arg in args)


def cache_decorator(expire: int = 3600):
    """
    Fonksiyonları cache'lemek için dekoratör.
    
    Args:
        expire: Cache süresi (saniye)
        
    Returns:
        Dekoratör fonksiyonu
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Cache anahtarı oluştur
            cache_key = f"{func.__module__}.{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Cache'ten veriyi al
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Fonksiyonu çalıştır
            result = func(*args, **kwargs)
            
            # Sonucu cache'e kaydet
            set_cache(cache_key, result, expire)
            
            return result
        return wrapper
    return decorator 


# Mock Redis implementation for when Redis is not available
class MockRedis:
    def __init__(self):
        self._cache = {}
        self._expires = {}
        logger.warning("Redis bağlantısı kurulamadı. Bellek içi önbellek kullanılıyor.")
    
    def ping(self):
        return True
    
    def get(self, key):
        if key in self._cache:
            return self._cache[key]
        return None
    
    def set(self, key, value, ex=None):
        self._cache[key] = value
        if ex:
            self._expires[key] = ex
        return True
    
    def delete(self, *keys):
        for key in keys:
            if key in self._cache:
                del self._cache[key]
            if key in self._expires:
                del self._expires[key]
        return True
    
    def exists(self, key):
        # Return bool to match Redis behavior
        return bool(key in self._cache)
    
    def keys(self, pattern):
        import re
        pattern = pattern.replace('*', '.*')
        pattern_obj = re.compile(pattern)
        return [key for key in self._cache.keys() if pattern_obj.match(key)]
    
    def expire(self, key, seconds):
        if key in self._cache:
            self._expires[key] = seconds
            return True
        return False
    
    def ttl(self, key):
        if key in self._expires:
            return self._expires[key]
        return -1
    
    def flushall(self):
        self._cache.clear()
        self._expires.clear()
        return True
    
    def close(self):
        pass


class MockRedisPool:
    def __init__(self):
        self._cache = {}
        self._expires = {}
    
    async def get(self, key):
        if key in self._cache:
            return self._cache[key]
        return None
    
    async def set(self, key, value, ex=None):
        self._cache[key] = value
        if ex:
            self._expires[key] = ex
        return True
    
    async def expire(self, key, time):
        if key in self._cache:
            self._expires[key] = time
            return True
        return False
    
    async def delete(self, *keys):
        for key in keys:
            if key in self._cache:
                del self._cache[key]
            if key in self._expires:
                del self._expires[key]
        return True
    
    async def exists(self, key):
        # Return bool to match Redis behavior
        return bool(key in self._cache)
    
    async def keys(self, pattern):
        import re
        pattern = pattern.replace('*', '.*')
        pattern_obj = re.compile(pattern)
        return [key for key in self._cache.keys() if pattern_obj.match(key)]
    
    async def ttl(self, key):
        if key in self._expires:
            return self._expires[key]
        return -1
    
    async def flushall(self):
        self._cache.clear()
        self._expires.clear()
        return True
    
    async def close(self):
        pass
    
    async def ping(self):
        return True


class RedisCache:
    """Redis cache wrapper class."""
    
    def __init__(self, redis_client):
        """Initialize Redis cache.
        
        Args:
            redis_client: Redis client instance
        """
        self._redis = redis_client

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to store
            expire: Optional expiration time in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            elif not isinstance(value, str):
                value = str(value)
                
            await self._redis.set(key, value)
            if expire:
                await self._redis.expire(key, expire)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None
        """
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
                
            if isinstance(value, bytes):
                return value.decode('utf-8')
            return value
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful
        """
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists
        """
        try:
            result = await self._redis.exists(key)
            # Redis.exists returns an integer (1 if key exists, 0 if not)
            # Convert to boolean for consistent behavior
            return bool(result)
        except Exception as e:
            logger.error(f"Redis exists error: {str(e)}")
            return False

    async def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a JSON value in cache.
        
        Args:
            key: Cache key
            value: Value to store as JSON
            expire: Optional expiration time in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, expire)
        except Exception as e:
            logger.error(f"Redis set_json error: {str(e)}")
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        """Get a JSON value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Deserialized JSON value or None
        """
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get_json error: {str(e)}")
            return None

    async def set_multiple(self, pairs: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Set multiple key-value pairs in cache.
        
        Args:
            pairs: Dictionary of key-value pairs
            expire: Optional expiration time in seconds
            
        Returns:
            bool: True if all operations successful
        """
        try:
            for key, value in pairs.items():
                success = await self.set(key, value, expire)
                if not success:
                    return False
            return True
        except Exception as e:
            logger.error(f"Redis set_multiple error: {str(e)}")
            return False

    async def get_multiple(self, keys: List[str]) -> List[Any]:
        """Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            List[Any]: List of cached values
        """
        try:
            values = []
            for key in keys:
                value = await self.get(key)
                values.append(value)
            return values
        except Exception as e:
            logger.error(f"Redis get_multiple error: {str(e)}")
            return []

    async def delete_multiple(self, keys: List[str]) -> bool:
        """Delete multiple keys from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            bool: True if all operations successful
        """
        try:
            for key in keys:
                success = await self.delete(key)
                if not success:
                    return False
            return True
        except Exception as e:
            logger.error(f"Redis delete_multiple error: {str(e)}")
            return False

    async def clear(self) -> bool:
        """Clear all cache data.
        
        Returns:
            bool: True if successful
        """
        try:
            await self._redis.flushall()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {str(e)}")
            return False

    async def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            bool: True if successful
        """
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self.delete_multiple(keys)
            return True
        except Exception as e:
            logger.error(f"Redis delete_pattern error: {str(e)}")
            return False 