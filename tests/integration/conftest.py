import pytest_asyncio

import rapyer


@pytest_asyncio.fixture
async def redis_client():
    meta_redis = rapyer.BaseRedisModel.Meta.redis
    redis = meta_redis.from_url("redis://localhost:6370/0")
    await redis.flushdb()
    yield redis
    await redis.flushdb()
