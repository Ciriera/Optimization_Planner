from functools import wraps
from typing import Callable
from app.core.cache import redis_cache

def cache(ttl: int = None):
    """Redis cache dekoratörü"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Cache key oluştur
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Cache'de var mı kontrol et
            cached_data = redis_cache.get(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Fonksiyonu çalıştır ve sonucu cache'e kaydet
            result = await func(*args, **kwargs)
            redis_cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def clear_cache(pattern: str = None):
    """Cache temizleme dekoratörü"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Fonksiyonu çalıştır
            result = await func(*args, **kwargs)
            
            # Cache'i temizle
            if pattern:
                # TODO: Pattern'e göre cache temizleme
                pass
            else:
                redis_cache.clear()
            
            return result
        return wrapper
    return decorator 