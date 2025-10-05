import pytest_asyncio

import redis_pydantic


@pytest_asyncio.fixture
async def redis_client():
    redis = await redis_pydantic.BaseRedisModel.Meta.redis.from_url(
        "redis://localhost:6371/15"
    )
    await redis.flushdb()
    yield redis
    await redis.flushdb()
