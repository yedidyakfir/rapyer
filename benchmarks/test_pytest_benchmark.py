"""
Pytest-benchmark tests for Redis extraction methods comparison.
Compatible with CodSpeed and other benchmark tracking tools.
"""
import asyncio
import os
import pytest
from rapyer import AtomicRedisModel
from tests.models.simple_types import UserModelWithoutTTL


class BenchmarkContext:
    """Context manager for Redis setup and cleanup"""
    def __init__(self):
        self.redis = None
        
    async def __aenter__(self):
        # Setup Redis connection
        meta_redis = AtomicRedisModel.Meta.redis
        db_num = os.getenv("REDIS_DB", "0")
        self.redis = meta_redis.from_url(f"redis://localhost:6370/{db_num}", decode_responses=True)
        UserModelWithoutTTL.Meta.redis = self.redis
        
        # Create and save test data
        await self.redis.flushdb()
        models = [UserModelWithoutTTL(name=f"user_{i}", age=20 + i) for i in range(100)]
        await asyncio.gather(*[model.save() for model in models])
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup
        if self.redis:
            await self.redis.flushdb()
            await self.redis.aclose()


def benchmark_afind_extract():
    """Benchmark function for afind_extract method"""
    async def main():
        async with BenchmarkContext():
            return await UserModelWithoutTTL.afind()
    return asyncio.run(main())


def benchmark_each_key_extract():
    """Benchmark function for each_key_extract method"""
    async def main():
        async with BenchmarkContext():
            keys = await UserModelWithoutTTL.afind_keys()
            return await asyncio.gather(*[UserModelWithoutTTL.get(key) for key in keys])
    return asyncio.run(main())


def test_benchmark_afind_extract(benchmark):
    """Benchmark test for afind_extract method"""
    result = benchmark(benchmark_afind_extract)
    
    # Verify correctness
    assert len(result) == 100
    assert all(isinstance(item, UserModelWithoutTTL) for item in result)


def test_benchmark_each_key_extract(benchmark):
    """Benchmark test for each_key_extract method"""
    result = benchmark(benchmark_each_key_extract)
    
    # Verify correctness
    assert len(result) == 100
    assert all(isinstance(item, UserModelWithoutTTL) for item in result)


@pytest.mark.parametrize(
    "method_name,method_func",
    [
        ("afind_extract", benchmark_afind_extract),
        ("each_key_extract", benchmark_each_key_extract),
    ],
    ids=["afind_extract", "each_key_extract"]
)
def test_extraction_methods_comparison(benchmark, method_name, method_func):
    """Parametrized benchmark comparison test for CodSpeed integration"""
    result = benchmark(method_func)
    
    # Verify correctness
    assert len(result) == 100
    assert all(isinstance(item, UserModelWithoutTTL) for item in result)