import pytest_asyncio

import rapyer


@pytest_asyncio.fixture
async def redis_client():
    meta_redis = rapyer.AtomicRedisModel.Meta.redis
    redis = meta_redis.from_url("redis://localhost:6370/0", decode_responses=True)
    await redis.flushdb()
    yield redis
    await redis.flushdb()
