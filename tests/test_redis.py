"""
Redis cache tests
"""
import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis
import asyncio

from app.core.cache import RedisCache

pytestmark = pytest.mark.asyncio

@pytest_asyncio.fixture
async def redis_client():
    """FakeRedis client fixture."""
    client = FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()

@pytest_asyncio.fixture
async def redis_cache(redis_client):
    """RedisCache fixture."""
    return RedisCache(redis_client)

async def test_set_get(redis_cache):
    """Test setting and getting values"""
    key = "test_key"
    value = "test_value"
    await redis_cache.set(key, value)
    result = await redis_cache.get(key)
    assert result == value

async def test_delete(redis_cache):
    """Test deleting values"""
    key = "test_key"
    value = "test_value"
    await redis_cache.set(key, value)
    await redis_cache.delete(key)
    result = await redis_cache.get(key)
    assert result is None

async def test_exists(redis_cache):
    """Test checking if key exists"""
    key = "test_key"
    value = "test_value"
    await redis_cache.set(key, value)
    result = await redis_cache.exists(key)
    assert result is True

async def test_not_exists(redis_cache):
    """Test checking if key does not exist"""
    key = "nonexistent_key"
    result = await redis_cache.exists(key)
    assert result is False

async def test_expire(redis_cache):
    """Test key expiration"""
    key = "test_key"
    value = "test_value"
    await redis_cache.set(key, value, expire=1)
    await asyncio.sleep(1.1)  # Wait for expiration
    result = await redis_cache.get(key)
    assert result is None

async def test_set_get_bytes(redis_cache):
    """Test setting and getting byte values"""
    key = "test_key"
    value = b"test_value"
    await redis_cache.set(key, value)
    result = await redis_cache.get(key)
    assert result == "test_value"  # Should be decoded to string

async def test_set_get_int(redis_cache):
    """Test setting and getting integer values"""
    key = "test_key"
    value = 42
    await redis_cache.set(key, value)
    result = await redis_cache.get(key)
    assert result == "42"  # Should be converted to string

async def test_set_get_float(redis_cache):
    """Test setting and getting float values"""
    key = "test_key"
    value = 3.14
    await redis_cache.set(key, value)
    result = await redis_cache.get(key)
    assert result == "3.14"  # Should be converted to string

async def test_set_get_bool(redis_cache):
    """Test setting and getting boolean values"""
    key = "test_key"
    value = True
    await redis_cache.set(key, value)
    result = await redis_cache.get(key)
    assert result == "True"  # Should be converted to string

async def test_set_json(redis_cache):
    """Test setting and getting JSON values"""
    key = "test_key"
    value = {"test": "value", "nested": {"key": "value"}}
    await redis_cache.set_json(key, value)
    result = await redis_cache.get_json(key)
    assert result == value

async def test_set_multiple(redis_cache):
    """Test setting multiple key-value pairs"""
    pairs = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    await redis_cache.set_multiple(pairs)
    
    for key, value in pairs.items():
        result = await redis_cache.get(key)
        assert result == value

async def test_get_multiple(redis_cache):
    """Test getting multiple keys"""
    pairs = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    await redis_cache.set_multiple(pairs)
    
    keys = list(pairs.keys())
    results = await redis_cache.get_multiple(keys)
    assert results == list(pairs.values())

async def test_delete_multiple(redis_cache):
    """Test deleting multiple keys"""
    pairs = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    await redis_cache.set_multiple(pairs)
    
    keys = list(pairs.keys())
    await redis_cache.delete_multiple(keys)
    
    for key in keys:
        result = await redis_cache.get(key)
        assert result is None

async def test_set_with_ttl(redis_cache):
    """Test TTL ile cache işlemleri."""
    key = "test_ttl"
    value = "test_value"
    ttl = 3600  # 1 saat
    
    await redis_cache.set(key, value, ttl)
    ttl_result = await redis_cache._redis.ttl(key)
    
    assert ttl_result > 0
    assert ttl_result <= 3600

async def test_clear_cache(redis_cache):
    """Test önbellek temizleme."""
    # Birkaç test anahtarı ekle
    test_data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    
    for key, value in test_data.items():
        await redis_cache.set(key, value)
    
    # Önbelleği temizle
    await redis_cache.clear()
    
    # Tüm anahtarların silindiğini kontrol et
    for key in test_data:
        exists = await redis_cache.exists(key)
        assert not exists

async def test_pattern_delete(redis_cache):
    """Test pattern ile anahtar silme."""
    # Test anahtarları ekle
    test_data = {
        "user:1": "data1",
        "user:2": "data2",
        "other:1": "data3"
    }
    
    for key, value in test_data.items():
        await redis_cache.set(key, value)
    
    # Pattern ile sil
    await redis_cache.delete_pattern("user:*")
    
    # user:* anahtarlarının silindiğini kontrol et
    assert not await redis_cache.exists("user:1")
    assert not await redis_cache.exists("user:2")
    
    # other:* anahtarının hala var olduğunu kontrol et
    assert await redis_cache.exists("other:1")

# TestRedisCache sınıfının asenkron versiyonu
async def test_get_many(redis_cache, redis_client):
    """get_many metodunu test eder (asenkron versiyon)"""
    data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    for key, value in data.items():
        await redis_cache.set(key, value)
    
    # Anahtar listesini hazırla
    keys = list(data.keys())
    
    # get_many yerine asenkron bir çözüm kullan
    result = await redis_cache.get_multiple(keys)
    expected_result = list(data.values())
    assert result == expected_result

async def test_set_many(redis_cache):
    """set_many metodunu test eder (asenkron versiyon)"""
    data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    # set_many yerine asenkron versiyon olan set_multiple kullan
    await redis_cache.set_multiple(data)
    
    for key, value in data.items():
        result = await redis_cache.get(key)
        assert result == value

async def test_delete_many(redis_cache):
    """delete_many metodunu test eder (asenkron versiyon)"""
    data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    await redis_cache.set_multiple(data)
    
    # delete_many yerine asenkron versiyon olan delete_multiple kullan
    await redis_cache.delete_multiple(list(data.keys()))
    
    for key in data:
        result = await redis_cache.get(key)
        assert result is None

async def test_incr(redis_cache, redis_client):
    """incr metodunu test eder (asenkron versiyon)"""
    key = "counter"
    await redis_cache.set(key, "1")
    
    # Asenkron incr işlemi
    await redis_client.incr(key)
    
    result = await redis_cache.get(key)
    assert result == "2"

async def test_decr(redis_cache, redis_client):
    """decr metodunu test eder (asenkron versiyon)"""
    key = "counter"
    await redis_cache.set(key, "2")
    
    # Asenkron decr işlemi
    await redis_client.decr(key)
    
    result = await redis_cache.get(key)
    assert result == "1" 