import pytest
from app.core.cache import redis_client, get_cache, set_cache, delete_cache

def test_redis_connection():
    """Redis bağlantısını test et"""
    try:
        # Test verisi
        test_key = "test_key"
        test_value = {"name": "test", "value": 123}
        
        # Veriyi cache'e kaydet
        set_cache(test_key, test_value)
        
        # Veriyi cache'den oku
        cached_value = get_cache(test_key)
        assert cached_value == test_value
        
        # Veriyi cache'den sil
        delete_cache(test_key)
        assert get_cache(test_key) is None
        
        print("Redis bağlantı testi başarılı!")
        return True
    except Exception as e:
        print(f"Redis bağlantı testi başarısız: {e}")
        return False

if __name__ == "__main__":
    test_redis_connection() 