import fakeredis.aioredis
import pytest_asyncio

from redis_pydantic.base import RedisModel


@pytest_asyncio.fixture
async def redis_client():
    fake_redis = fakeredis.aioredis.FakeRedis()

    # Patch the Redis client in RedisModel Config
    original_redis = RedisModel.Meta.redis
    RedisModel.Meta.redis = fake_redis

    yield fake_redis

    # Clean up and restore original redis client
    await fake_redis.flushall()
    await fake_redis.aclose()
    RedisModel.Meta.redis = original_redis
