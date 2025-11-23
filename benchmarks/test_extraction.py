import asyncio
from datetime import datetime

import pytest
import pytest_asyncio

from rapyer import AtomicRedisModel
from tests.models.simple_types import UserModelWithoutTTL

COMPARE_FULL_EXTRACTION_NAME = "COMPARE_FULL_EXTRACTION_NAME"


@pytest_asyncio.fixture
async def setup_test_data():
    # Arrange - Create test data
    models = [UserModelWithoutTTL(name=f"user_{i}", age=20 + i) for i in range(100)]
    await asyncio.gather(*[model.save() for model in models])
    yield models


async def extract_each_key(redis_klass: type[AtomicRedisModel]):
    start = datetime.now()
    keys = await redis_klass.afind_keys()
    res = await asyncio.gather(*[redis_klass.get(key) for key in keys])
    end = datetime.now()
    delta = end - start
    print(delta)


async def afind_extract(redis_klass: type[AtomicRedisModel]):
    start = datetime.now()
    res = await redis_klass.afind()
    end = datetime.now()
    delta = end - start
    print(delta)


@pytest.mark.asyncio
@pytest.mark.parametrize("extract_method", [afind_extract, extract_each_key])
async def test_compare_full_extraction(benchmark, setup_test_data, extract_method):
    await benchmark(extract_method, UserModelWithoutTTL)
