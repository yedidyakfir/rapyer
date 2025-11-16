import redis.asyncio as redis_async
from rapyer.base import REDIS_MODELS
from redis.asyncio.client import Redis


async def init_rapyer(redis: str | Redis = None, ttl: int = None):
    if isinstance(redis, str):
        redis = redis_async.from_url(redis, decode_responses=True, max_connection=20)

    for model in REDIS_MODELS:
        if redis is not None:
            model.Meta.redis = redis
        if ttl is not None:
            model.Meta.ttl = ttl


async def teardown_rapyer():
    for model in REDIS_MODELS:
        if model.Meta.ttl is not None:
            await model.Meta.redis.aclose()
