import pytest
import pytest_asyncio

from rapyer.base import BaseRedisModel, RedisConfig


class UserModelWithTTL(BaseRedisModel):
    name: str = "test"
    age: int = 25
    active: bool = True
    tags: list[str] = []
    settings: dict[str, str] = {}

    Meta = RedisConfig(ttl=300)


class UserModelWithoutTTL(BaseRedisModel):
    name: str = "test"
    age: int = 25


@pytest_asyncio.fixture
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
