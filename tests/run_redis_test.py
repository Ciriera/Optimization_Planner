"""
Redis cache tests
"""
import asyncio
import json
import pytest
import pytest_asyncio
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

# Redis client fixture
@pytest_asyncio.fixture(scope="function")
async def redis_client():
    """Redis client fixture."""
    client = FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.close()

# Redis cache fixture
@pytest_asyncio.fixture(scope="function")
async def redis_cache(redis_client):
    """Redis cache fixture."""
    yield RedisCache(redis_client)

@pytest.mark.asyncio
async def test_set_get(redis_cache):
    """Test setting and getting values"""
    key = "test_key"
    value = "test_value"
    await redis_cache.set(key, value)
    result = await redis_cache.get(key)
    print(f"Expected: {value}, Got: {result}")
    assert result == value
    print("✅ test_set_get passed")

@pytest.mark.asyncio
async def test_delete(redis_cache):
    """Test deleting values"""
    key = "test_key"
    value = "test_value"
    
    # Set value
    await redis_cache.set(key, value)
    assert await redis_cache.get(key) == value
    
    # Delete value
    await redis_cache.delete(key)
    assert await redis_cache.get(key) is None
    print("✅ test_delete passed")

@pytest.mark.asyncio
async def test_exists(redis_cache):
    """Test key existence check"""
    key = "test_key"
    value = "test_value"
    
    # Key should not exist initially
    assert not await redis_cache.exists(key)
    
    # Set value and check existence
    await redis_cache.set(key, value)
    assert await redis_cache.exists(key)
    
    # Delete and check non-existence
    await redis_cache.delete(key)
    assert not await redis_cache.exists(key)
    print("✅ test_exists passed")

@pytest.mark.asyncio
async def test_expire(redis_cache):
    """Test key expiration"""
    key = "test_key"
    value = "test_value"
    
    # Set with short expiration
    await redis_cache.set(key, value, expire=1)
    assert await redis_cache.get(key) == value
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    
    # Key should be gone
    assert await redis_cache.get(key) is None
    print("✅ test_expire passed")

@pytest.mark.asyncio
async def test_set_json(redis_cache):
    """Test setting and getting JSON values"""
    key = "test_json"
    value = {"name": "Test", "value": 123}
    
    # Set JSON
    await redis_cache.set_json(key, value)
    
    # Get JSON
    result = await redis_cache.get_json(key)
    assert result == value
    print("✅ test_set_json passed")

@pytest.mark.asyncio
async def test_set_multiple(redis_cache):
    """Test setting multiple values"""
    pairs = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    
    # Set multiple
    await redis_cache.set_multiple(pairs)
    
    # Check each value
    for key, expected in pairs.items():
        assert await redis_cache.get(key) == expected
    
    print("✅ test_set_multiple passed")

@pytest.mark.asyncio
async def test_get_multiple(redis_cache):
    """Test getting multiple values"""
    pairs = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    
    # Set values
    await redis_cache.set_multiple(pairs)
    
    # Get multiple
    keys = list(pairs.keys())
    values = await redis_cache.get_multiple(keys)
    
    # Check values
    for i, key in enumerate(keys):
        assert values[i] == pairs[key]
    
    print("✅ test_get_multiple passed")

@pytest.mark.asyncio
async def test_delete_multiple(redis_cache):
    """Test deleting multiple values"""
    pairs = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    
    # Set values
    await redis_cache.set_multiple(pairs)
    
    # Delete first two keys
    keys_to_delete = list(pairs.keys())[:2]
    await redis_cache.delete_multiple(keys_to_delete)
    
    # Check deleted keys
    for key in keys_to_delete:
        assert await redis_cache.get(key) is None
    
    # Check remaining key
    remaining_key = list(pairs.keys())[2]
    assert await redis_cache.get(remaining_key) == pairs[remaining_key]
    
    print("✅ test_delete_multiple passed")

@pytest.mark.asyncio
async def test_set_with_ttl(redis_cache):
    """Test setting values with TTL"""
    key = "test_ttl"
    value = "test_value"
    
    # Set with TTL
    await redis_cache.set(key, value, expire=2)
    
    # Check value exists
    assert await redis_cache.get(key) == value
    
    # Wait for half the TTL
    await asyncio.sleep(1)
    assert await redis_cache.get(key) == value
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    assert await redis_cache.get(key) is None
    
    print("✅ test_set_with_ttl passed")

@pytest.mark.asyncio
async def test_clear_cache(redis_cache):
    """Test clearing the cache"""
    # Set multiple values
    pairs = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    await redis_cache.set_multiple(pairs)
    
    # Verify values exist
    for key, expected in pairs.items():
        assert await redis_cache.get(key) == expected
    
    # Clear cache
    await redis_cache.clear()
    
    # Verify all values are gone
    for key in pairs:
        assert await redis_cache.get(key) is None
    
    print("✅ test_clear_cache passed")

@pytest.mark.asyncio
async def test_pattern_delete(redis_cache):
    """Test deleting by pattern"""
    # Set values with pattern
    await redis_cache.set("user:1", "Alice")
    await redis_cache.set("user:2", "Bob")
    await redis_cache.set("user:3", "Charlie")
    await redis_cache.set("product:1", "Apple")
    
    # Delete by pattern
    await redis_cache.delete_pattern("user:*")
    
    # Check user keys are gone
    assert await redis_cache.get("user:1") is None
    assert await redis_cache.get("user:2") is None
    assert await redis_cache.get("user:3") is None
    
    # Check product key still exists
    assert await redis_cache.get("product:1") == "Apple"
    
    print("✅ test_pattern_delete passed")

# Bu fonksiyonu doğrudan çalıştırma için saklıyoruz
async def run_tests():
    """Run all tests"""
    print("=" * 50)
    print("Redis Cache Tests")
    print("=" * 50)
    
    client = FakeRedis(decode_responses=True)
    cache = RedisCache(client)
    
    tests = [
        test_set_get(cache),
        test_delete(cache),
        test_exists(cache),
        test_expire(cache),
        test_set_json(cache),
        test_set_multiple(cache),
        test_get_multiple(cache),
        test_delete_multiple(cache),
        test_set_with_ttl(cache),
        test_clear_cache(cache),
        test_pattern_delete(cache)
    ]
    
    await asyncio.gather(*tests)
    
    await client.close()
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_tests()) 