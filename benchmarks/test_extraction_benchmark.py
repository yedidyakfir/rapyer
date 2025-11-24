import asyncio
import os
import pytest
from rapyer import AtomicRedisModel
from tests.models.simple_types import UserModelWithoutTTL


@pytest.fixture(scope="function")
async def redis_with_test_data():
    """Set up Redis connection and populate with test data"""
    # Set up Redis connection
    meta_redis = AtomicRedisModel.Meta.redis
    db_num = os.getenv("REDIS_DB", "0")
    redis = meta_redis.from_url(
        f"redis://localhost:6370/{db_num}", decode_responses=True
    )
    UserModelWithoutTTL.Meta.redis = redis

    # Create and save test data
    await redis.flushdb()
    models = [UserModelWithoutTTL(name=f"user_{i}", age=20 + i) for i in range(100)]
    await asyncio.gather(*[model.save() for model in models])

    yield models

    # Cleanup
    await redis.flushdb()
    await redis.aclose()  # Don't forget to close the connection!


async def afind_extract():
    return await UserModelWithoutTTL.afind()


async def each_key_extract():
    keys = await UserModelWithoutTTL.afind_keys()
    return await asyncio.gather(*[UserModelWithoutTTL.get(key) for key in keys])


@pytest.mark.parametrize(
    "method_name,method_func",
    [
        ("afind_extract", afind_extract),
        ("extract_each_key", each_key_extract),
    ],
)
@pytest.mark.benchmark(group="extraction")
@pytest.mark.asyncio
async def test_compare_extraction_methods(
    async_benchmark, redis_with_test_data, method_name, method_func
):
    """Compare performance of different extraction methods"""
    # The fixture ensures data is ready before benchmarking starts

    # Benchmark only the extraction method
    result = await async_benchmark(method_func)

    # Verify correctness
    assert len(result) == 100
    assert all(isinstance(item, UserModelWithoutTTL) for item in result)
