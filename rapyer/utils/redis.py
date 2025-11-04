import asyncio
import contextlib
import uuid
from datetime import timedelta

from redis.asyncio import Redis


@contextlib.asynccontextmanager
async def acquire_lock(
    redis: Redis, key: str, lock_timeout: timedelta | int = 10, sleep_time: int = 0.1
):
    lock_key = f"{key}:lock"
    lock_token = str(uuid.uuid4())
    while not await redis.set(lock_key, lock_token, nx=True, ex=lock_timeout):
        await asyncio.sleep(sleep_time)
    try:
        yield
    finally:
        await redis.delete(lock_key)


def update_keys_in_pipeline(pipeline, redis_key: str, **kwargs):
    for json_path, value in kwargs.items():
        pipeline.json().set(redis_key, json_path, value)
