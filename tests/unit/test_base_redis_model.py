import fakeredis.aioredis
import pytest
import pytest_asyncio

import redis_pydantic
from redis_pydantic.base import BaseRedisModel
from redis_pydantic.types import ALL_TYPES


class UserModel(BaseRedisModel):
    tags: list[str] = []

    class Meta:
        redis = None  # Will be set in fixture
        redis_type = ALL_TYPES


@pytest_asyncio.fixture
async def real_redis_client():
    redis = await redis_pydantic.RedisModel.Meta.redis.from_url(
        "redis://localhost:6371/0"
    )
    UserModel.Meta.redis = redis
    await redis.flushall()
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest.mark.asyncio
async def test_base_redis_model__list_append__check_redis_append(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag2"])
    await user.save()

    # Act
    await user.tags.append("tags")

    # Assert
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert actual_lst[0] == user.tags
