import pytest
from app.core.cache import RedisCache
from app.core.config import settings
import fakeredis
import json

@pytest.fixture
def redis_client():
    """Fake Redis client fixture"""
    return fakeredis.FakeStrictRedis()

@pytest.fixture
def redis_cache(redis_client):
    """Redis cache fixture"""
    return RedisCache(redis_client)

def test_redis_set_get(redis_cache):
    """Test Redis set ve get işlemleri"""
    key = "test_key"
    value = {"data": "test_value"}
    
    # Set işlemi
    redis_cache.set(key, value, expire=60)
    
    # Get işlemi
    result = redis_cache.get(key)
    assert result == value

def test_redis_delete(redis_cache):
    """Test Redis delete işlemi"""
    key = "test_key"
    value = {"data": "test_value"}
    
    # Set ve delete işlemleri
    redis_cache.set(key, value)
    redis_cache.delete(key)
    
    # Key silinmiş olmalı
    result = redis_cache.get(key)
    assert result is None

def test_redis_expire(redis_cache, redis_client):
    """Test Redis expire işlemi"""
    key = "test_key"
    value = {"data": "test_value"}
    
    # Set with expire
    redis_cache.set(key, value, expire=1)
    
    # Key var olmalı
    assert redis_cache.get(key) == value
    
    # TTL kontrolü
    ttl = redis_client.ttl(key)
    assert ttl > 0

def test_redis_json_serialization(redis_cache):
    """Test Redis JSON serializasyon"""
    key = "test_key"
    value = {"list": [1, 2, 3], "dict": {"a": 1, "b": 2}}
    
    # Set complex object
    redis_cache.set(key, value)
    
    # Get and verify
    result = redis_cache.get(key)
    assert result == value
    assert isinstance(result["list"], list)
    assert isinstance(result["dict"], dict) 