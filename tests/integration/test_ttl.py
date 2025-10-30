import pytest
import pytest_asyncio

from tests.models.simple_types import UserModelWithTTL, UserModelWithoutTTL


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    UserModelWithTTL.Meta.redis = redis_client
    UserModelWithoutTTL.Meta.redis = redis_client

    yield redis_client
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_base_redis_model_with_ttl__save__check_ttl_set_sanity(real_redis_client):
    # Arrange
    user = UserModelWithTTL(name="john", age=30)

    # Act
    await user.save()

    # Assert
    ttl = await real_redis_client.ttl(user.key)
    assert ttl > 0
    assert ttl <= 300


@pytest.mark.asyncio
async def test_base_redis_model_without_ttl__save__check_no_ttl_set_sanity(
    real_redis_client,
):
    # Arrange
    user = UserModelWithoutTTL(name="john", age=30)

    # Act
    await user.save()

    # Assert
    ttl = await real_redis_client.ttl(user.key)
    assert ttl == -1
