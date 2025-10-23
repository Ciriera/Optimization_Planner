"""
Rate limiting implementation using Redis.
"""
import time
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from app.core.config import settings


class RateLimiter:
    """Redis-based rate limiter."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def init_redis(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis_client = None
    
    async def is_rate_limited(
        self, 
        key: str, 
        limit: int = 100, 
        window: int = 60
    ) -> bool:
        """
        Check if request is rate limited.
        
        Args:
            key: Unique identifier (user_id, ip, etc.)
            limit: Maximum requests per window
            window: Time window in seconds
            
        Returns:
            True if rate limited, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, window)
            
            results = await pipe.execute()
            current_count = results[1]
            
            return current_count >= limit
            
        except Exception as e:
            print(f"Rate limiting error: {e}")
            return False
    
    async def get_remaining_requests(
        self, 
        key: str, 
        limit: int = 100, 
        window: int = 60
    ) -> int:
        """Get remaining requests for a key."""
        if not self.redis_client:
            return limit
        
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            await self.redis_client.zremrangebyscore(key, 0, window_start)
            current_count = await self.redis_client.zcard(key)
            
            return max(0, limit - current_count)
            
        except Exception as e:
            print(f"Rate limiting error: {e}")
            return limit


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request) -> None:
    """Middleware function to check rate limits."""
    # Get client identifier
    client_ip = request.client.host
    user_id = getattr(request.state, "user_id", None)
    
    # Use user_id if available, otherwise use IP
    key = f"rate_limit:{user_id or client_ip}"
    
    # Check rate limit (100 requests per minute)
    is_limited = await rate_limiter.is_rate_limited(key, limit=100, window=60)
    
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0"
            }
        )


async def get_rate_limit_info(request: Request) -> dict:
    """Get rate limit information for a request."""
    client_ip = request.client.host
    user_id = getattr(request.state, "user_id", None)
    key = f"rate_limit:{user_id or client_ip}"
    
    remaining = await rate_limiter.get_remaining_requests(key, limit=100, window=60)
    
    return {
        "limit": 100,
        "remaining": remaining,
        "reset_time": int(time.time()) + 60
    }
