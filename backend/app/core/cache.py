import functools
from typing import Any, Callable, Optional
import json
import logging
from redis import Redis
from redis.exceptions import RedisError
import aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis bağlantısı
try:
    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )
    redis_client.ping()  # Bağlantıyı test et
    logger.info("Redis bağlantısı başarılı")
except RedisError as e:
    logger.warning(f"Redis bağlantısı kurulamadı: {e}")
    # Mock redis client
    class MockRedis:
        def __init__(self):
            self._cache = {}
        
        def get(self, key):
            return self._cache.get(key)
            
        def setex(self, name, time, value):
            self._cache[name] = value
            
        def delete(self, *keys):
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
                    
        def keys(self, pattern="*"):
            return [k for k in self._cache.keys() if pattern == "*" or k.startswith(pattern)]
            
    redis_client = MockRedis()
    logger.info("Mock Redis kullanılıyor")

# Async Redis için bağlantı havuzu
redis_pool = None

async def init_redis_pool():
    """
    Redis bağlantı havuzunu başlat
    """
    global redis_pool
    try:
        redis_pool = await aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Async Redis bağlantı havuzu başlatıldı")
    except Exception as e:
        logger.error(f"Async Redis bağlantı havuzu oluşturulamadı: {e}")

def cache(ttl: int = 300):
    """Redis cache dekoratörü
    
    Args:
        ttl: Cache süresi (saniye)
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Cache anahtarını oluştur
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Cache'den veriyi almaya çalış
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
            # Fonksiyonu çalıştır ve sonucu cache'le
            result = func(*args, **kwargs)
            redis_client.setex(
                name=cache_key,
                time=ttl,
                value=json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str = "*"):
    """Cache'i temizle
    
    Args:
        pattern: Silinecek anahtarların deseni
    """
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)

def get_cached_value(key: str) -> Any:
    """Cache'den değer al"""
    value = redis_client.get(key)
    return json.loads(value) if value else None

def set_cached_value(key: str, value: Any, ttl: int = 300):
    """Cache'e değer kaydet"""
    redis_client.setex(
        name=key,
        time=ttl,
        value=json.dumps(value)
    )

def delete_cached_value(key: str):
    """Cache'den değer sil"""
    redis_client.delete(key)

class RedisCache:
    """Redis cache implementation"""
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """Set a key-value pair in Redis with optional expiration"""
        serialized_value = json.dumps(value)
        if expire:
            self.redis.setex(key, expire, serialized_value)
        else:
            self.redis.set(key, serialized_value)

    def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis by key"""
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    def delete(self, key: str) -> None:
        """Delete a key from Redis"""
        self.redis.delete(key)

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        return bool(self.redis.exists(key))

    def expire(self, key: str, seconds: int) -> None:
        """Set expiration time for a key"""
        self.redis.expire(key, seconds)

    def ttl(self, key: str) -> int:
        """Get remaining time to live for a key"""
        return self.redis.ttl(key)

    def flush_all(self) -> None:
        """Delete all keys in Redis"""
        self.redis.flushall()

    def get_keys(self, pattern: str = "*") -> list:
        """Get all keys matching pattern"""
        return [key.decode() for key in self.redis.keys(pattern)] 