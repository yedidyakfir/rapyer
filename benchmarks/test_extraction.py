import asyncio
import pytest
import pytest_asyncio
from tests.models.simple_types import UserModelWithoutTTL

COMPARE_FULL_EXTRACTION_NAME = "COMPARE_FULL_EXTRACTION_NAME"


@pytest_asyncio.fixture
async def setup_test_data():
    # Arrange - Create test data
    models = [UserModelWithoutTTL(name=f"user_{i}", age=20 + i) for i in range(100)]
    await asyncio.gather(*[model.save() for model in models])
    yield models
    # Cleanup
    keys = await UserModelWithoutTTL.afind_keys()
    if keys:
        await asyncio.gather(*[UserModelWithoutTTL.delete_by_key(key) for key in keys])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "setup_benchmark", [COMPARE_FULL_EXTRACTION_NAME], indirect=True
)
async def test_afind_benchmark(setup_benchmark, setup_test_data):
    res = await UserModelWithoutTTL.afind()
    assert len(res) == len(setup_test_data)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "setup_benchmark", [COMPARE_FULL_EXTRACTION_NAME], indirect=True
)
async def test_afind_keys_with_gather_benchmark(setup_benchmark, setup_test_data):
    keys = await UserModelWithoutTTL.afind_keys()
    res = await asyncio.gather(*[UserModelWithoutTTL.get(key) for key in keys])
    assert len(res) == len(setup_test_data)
