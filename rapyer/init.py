import redis.asyncio as redis_async
from redis.asyncio.client import Redis

from rapyer.base import REDIS_MODELS


def init_rapyer(redis: str | Redis, ttl: int = None):
    if isinstance(redis, str):
        redis = redis_async.from_url(redis)

    for model in REDIS_MODELS:
        model.Meta.redis = redis
        model.Meta.ttl = ttl
