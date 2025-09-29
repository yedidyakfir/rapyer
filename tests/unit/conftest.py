import pytest_asyncio
import fakeredis.aioredis
from redis_pydantic.base import RedisModel


@pytest_asyncio.fixture
async def redis_client():
    fake_redis = fakeredis.aioredis.FakeRedis()
    
    # Patch the Redis client in RedisModel Config
    original_redis = RedisModel.Config.redis
    RedisModel.Config.redis = fake_redis
    
    yield fake_redis
    
    # Clean up and restore original redis client
    await fake_redis.flushall()
    await fake_redis.aclose()
    RedisModel.Config.redis = original_redis