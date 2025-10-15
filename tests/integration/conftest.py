import pytest_asyncio

import redis_pydantic


@pytest_asyncio.fixture
async def redis_client():
    meta_redis = redis_pydantic.BaseRedisModel.Meta.redis
    redis = meta_redis.from_url("redis://localhost:6370/0")
    await redis.flushdb()
    yield redis
    await redis.flushdb()
