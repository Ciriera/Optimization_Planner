"""
Redis cache tests
"""
import asyncio
import json
from fakeredis.aioredis import FakeRedis

class RedisCache:
    """Redis önbellek sınıfı."""
    
    def __init__(self, redis_client):
        """
        Initialize Redis cache.
        
        Args:
            redis_client: Redis client
        """
        self._redis = redis_client
    
    async def set(self, key: str, value: any, expire: int = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
            
        Returns:
            bool: Success status
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await self._redis.set(key, value)
            if expire:
                await self._redis.expire(key, expire)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    async def get(self, key: str) -> any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Any: Cached value or None
        """
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: Success status
        """
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if exists
        """
        try:
            return bool(await self._redis.exists(key))
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    async def set_json(self, key: str, value: any, expire: int = None) -> bool:
        """
        Set a JSON value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
            
        Returns:
            bool: Success status
        """
        try:
            serialized = json.dumps(value)
            await self._redis.set(key, serialized)
            if expire:
                await self._redis.expire(key, expire)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    async def get_json(self, key: str) -> any:
        """
        Get a JSON value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Any: Cached value or None
        """
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    async def set_multiple(self, pairs: dict, expire: int = None) -> bool:
        """
        Set multiple values in the cache.
        
        Args:
            pairs: Dict of key-value pairs
            expire: Expiration time in seconds
            
        Returns:
            bool: Success status
        """
        try:
            for key, value in pairs.items():
                await self.set(key, value, expire)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    async def get_multiple(self, keys: list) -> list:
        """
        Get multiple values from the cache.
        
        Args:
            keys: List of keys
            
        Returns:
            List[Any]: List of values
        """
        try:
            result = []
            for key in keys:
                result.append(await self.get(key))
            return result
        except Exception as e:
            print(f"Error: {e}")
            return [None] * len(keys)
    
    async def delete_multiple(self, keys: list) -> bool:
        """
        Delete multiple values from the cache.
        
        Args:
            keys: List of keys
            
        Returns:
            bool: Success status
        """
        try:
            for key in keys:
                await self.delete(key)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear all keys in the database.
        
        Returns:
            bool: Success status
        """
        try:
            await self._redis.flushall()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> bool:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            bool: Success status
        """
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                for key in keys:
                    await self.delete(key)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

async def test_set_get():
    """Test setting and getting values"""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
    key = "test_key"
    value = "test_value"
    await redis_cache.set(key, value)
    result = await redis_cache.get(key)
    print(f"Expected: {value}, Got: {result}")
    assert result == value
    print("✅ test_set_get passed")
    
    await client.flushall()
    await client.close()

async def test_delete():
    """Test deleting values"""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
    key = "test_key"
    value = "test_value"
    await redis_cache.set(key, value)
    await redis_cache.delete(key)
    result = await redis_cache.get(key)
    assert result is None
    print("✅ test_delete passed")
    
    await client.flushall()
    await client.close()

async def test_exists():
    """Test checking if key exists"""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
    key = "test_key"
    value = "test_value"
    await redis_cache.set(key, value)
    exists = await redis_cache.exists(key)
    assert exists is True
    
    await redis_cache.delete(key)
    exists = await redis_cache.exists(key)
    assert exists is False
    print("✅ test_exists passed")
    
    await client.flushall()
    await client.close()

async def test_expire():
    """Test setting expiration on keys"""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
    key = "test_key"
    value = "test_value"
    await redis_cache.set(key, value, expire=1)  # 1 second expiration
    result = await redis_cache.get(key)
    assert result == value
    
    await asyncio.sleep(2)  # Wait for expiration
    result = await redis_cache.get(key)
    assert result is None
    print("✅ test_expire passed")
    
    await client.flushall()
    await client.close()

async def test_set_json():
    """Test setting and getting JSON values"""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
    key = "test_key"
    value = {"test": "value", "nested": {"key": "value"}}
    await redis_cache.set_json(key, value)
    result = await redis_cache.get_json(key)
    assert result == value
    print("✅ test_set_json passed")
    
    await client.flushall()
    await client.close()

async def test_set_multiple():
    """Test setting multiple key-value pairs"""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
    pairs = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    await redis_cache.set_multiple(pairs)
    
    for key, value in pairs.items():
        result = await redis_cache.get(key)
        assert result == value
    print("✅ test_set_multiple passed")
    
    await client.flushall()
    await client.close()

async def test_get_multiple():
    """Test getting multiple keys"""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
    pairs = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    await redis_cache.set_multiple(pairs)
    
    keys = list(pairs.keys())
    results = await redis_cache.get_multiple(keys)
    assert results == list(pairs.values())
    print("✅ test_get_multiple passed")
    
    await client.flushall()
    await client.close()

async def test_delete_multiple():
    """Test deleting multiple keys"""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
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
    print("✅ test_delete_multiple passed")
    
    await client.flushall()
    await client.close()

async def test_set_with_ttl():
    """Test TTL ile cache işlemleri."""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
    key = "test_ttl"
    value = "test_value"
    ttl = 3600  # 1 saat
    
    await redis_cache.set(key, value, ttl)
    ttl_result = await client.ttl(key)
    
    assert ttl_result > 0
    assert ttl_result <= 3600
    print("✅ test_set_with_ttl passed")
    
    await client.flushall()
    await client.close()

async def test_clear_cache():
    """Test önbellek temizleme."""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
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
    print("✅ test_clear_cache passed")
    
    await client.flushall()
    await client.close()

async def test_pattern_delete():
    """Test pattern ile anahtar silme."""
    client = FakeRedis(decode_responses=True)
    redis_cache = RedisCache(client)
    
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
    print("✅ test_pattern_delete passed")
    
    await client.flushall()
    await client.close()

async def run_tests():
    """Run all tests"""
    print("Running Redis cache tests...")
    await test_set_get()
    await test_delete()
    await test_exists()
    await test_expire()
    await test_set_json()
    await test_set_multiple()
    await test_get_multiple()
    await test_delete_multiple()
    await test_set_with_ttl()
    await test_clear_cache()
    await test_pattern_delete()
    print("All tests passed! ✅")

if __name__ == "__main__":
    asyncio.run(run_tests()) 