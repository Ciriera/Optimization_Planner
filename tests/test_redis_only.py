"""
Redis test script - run directly to test Redis connection

Usage:
  python test_redis_only.py

Dependencies:
  - redis
  - aioredis
"""

import os
import asyncio
import redis
import aioredis
import json
from typing import Optional, Any

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Sync Redis client
redis_client = None

# Async Redis pool
redis_pool = None


async def init_redis():
    """Initialize Redis connections"""
    global redis_client, redis_pool
    
    print(f"Bağlantı kurulacak Redis sunucusu: {REDIS_HOST}:{REDIS_PORT}")
    
    try:
        # Initialize sync Redis client
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD if REDIS_PASSWORD else None,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # Test sync connection
        redis_client.ping()
        print("✅ Senkron Redis bağlantısı başarılı")
        
        # Initialize async Redis pool
        redis_pool = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test async connection with a simple command
        await redis_pool.ping()
        print("✅ Asenkron Redis bağlantısı başarılı")
        
        return True
    except Exception as e:
        print(f"❌ Redis bağlantısı başarısız: {e}")
        return False


def test_sync_redis():
    """Test synchronous Redis operations"""
    if not redis_client:
        print("Redis client not initialized")
        return False
    
    try:
        # Test data
        test_key = "test_sync_key"
        test_value = {"name": "test", "value": 123}
        
        # Store data in Redis
        redis_client.set(test_key, json.dumps(test_value))
        
        # Retrieve data from Redis
        cached_value = redis_client.get(test_key)
        if cached_value:
            cached_value = json.loads(cached_value)
        
        # Verify data
        assert cached_value == test_value, f"Expected {test_value}, got {cached_value}"
        
        # Delete data
        redis_client.delete(test_key)
        
        # Verify deletion
        assert redis_client.get(test_key) is None, "Key should not exist after deletion"
        
        print("✅ Senkron Redis testi başarılı")
        return True
    except Exception as e:
        print(f"❌ Senkron Redis testi başarısız: {e}")
        return False


async def test_async_redis():
    """Test asynchronous Redis operations"""
    if not redis_pool:
        print("Redis pool not initialized")
        return False
    
    try:
        # Test data
        test_key = "test_async_key"
        test_value = {"name": "async_test", "value": 456}
        
        # Store data in Redis
        await redis_pool.set(test_key, json.dumps(test_value))
        
        # Retrieve data from Redis
        cached_value = await redis_pool.get(test_key)
        if cached_value:
            cached_value = json.loads(cached_value)
        
        # Verify data
        assert cached_value == test_value, f"Expected {test_value}, got {cached_value}"
        
        # Delete data
        await redis_pool.delete(test_key)
        
        # Verify deletion
        assert await redis_pool.get(test_key) is None, "Key should not exist after deletion"
        
        print("✅ Asenkron Redis testi başarılı")
        return True
    except Exception as e:
        print(f"❌ Asenkron Redis testi başarısız: {e}")
        return False


async def main():
    """Main test function"""
    print("="*50)
    print("Redis Bağlantı Testi")
    print("="*50)
    
    # Initialize Redis
    if not await init_redis():
        print("Redis bağlantısı kurulamadı. Test sonlandırılıyor.")
        return
    
    # Run sync test
    test_sync_redis()
    
    # Run async test
    await test_async_redis()
    
    # Clean up
    print("\nBağlantılar kapatılıyor...")
    if redis_client:
        redis_client.close()
    if redis_pool:
        await redis_pool.close()
    
    print("="*50)
    print("Redis testi tamamlandı.")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main()) 