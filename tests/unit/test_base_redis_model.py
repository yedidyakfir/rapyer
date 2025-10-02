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
    await user.tags.append("tag3")

    # Assert
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert "tag3" in actual_lst[0]
    assert "tag3" in user.tags
    assert len(actual_lst[0]) == 3


@pytest.mark.asyncio
async def test_base_redis_model__list_extend__check_redis_extend(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1"])
    await user.save()

    # Act
    await user.tags.extend(["tag2", "tag3", "tag4"])

    # Assert
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert len(actual_lst[0]) == 4
    assert len(user.tags) == 4
    assert all(tag in actual_lst[0] for tag in ["tag1", "tag2", "tag3", "tag4"])
    assert all(tag in user.tags for tag in ["tag1", "tag2", "tag3", "tag4"])


@pytest.mark.asyncio
async def test_base_redis_model__comprehensive_operations__check_redis_sync(
    real_redis_client,
):
    # Arrange
    user = UserModel(tags=["initial"])
    await user.save()

    # Act
    await user.tags.append("tag1")
    await user.tags.extend(["tag2", "tag3"])
    await user.tags.insert(1, "inserted")

    # Assert
    # Check local state
    assert len(user.tags) == 5
    assert "initial" in user.tags
    assert "tag1" in user.tags
    assert "tag2" in user.tags
    assert "tag3" in user.tags
    assert "inserted" in user.tags

    # Check Redis state
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert len(actual_lst[0]) == 5
    assert all(
        tag in actual_lst[0] for tag in ["initial", "tag1", "tag2", "tag3", "inserted"]
    )

    # Test clear operation
    await user.tags.clear()
    assert len(user.tags) == 0
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert actual_lst is None or len(actual_lst) == 0 or len(actual_lst[0]) == 0


@pytest.mark.asyncio
async def test_base_redis_model__list_insert__check_redis_insert(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag3"])
    await user.save()

    # Act
    await user.tags.insert(1, "tag2")

    # Assert
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert len(actual_lst[0]) == 3
    assert len(user.tags) == 3
    assert actual_lst[0][1] == "tag2"
    assert user.tags[1] == "tag2"
    assert actual_lst[0] == ["tag1", "tag2", "tag3"]


@pytest.mark.asyncio
async def test_base_redis_model__list_clear__check_redis_clear(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag2", "tag3"])
    await user.save()

    # Act
    await user.tags.clear()

    # Assert
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert actual_lst is None or len(actual_lst) == 0 or len(actual_lst[0]) == 0
    assert len(user.tags) == 0


@pytest.mark.asyncio
async def test_base_redis_model__save__check_redis_save(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag2"])

    # Act
    await user.save()

    # Assert
    actual_data = await real_redis_client.json().get(user.key, "$")
    assert actual_data[0]["tags"] == ["tag1", "tag2"]
    assert actual_data[0]["tags"] == user.tags


@pytest.mark.asyncio
async def test_base_redis_model__load__check_redis_load(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag2"])
    await user.save()
    # Modify Redis directly
    await real_redis_client.json().arrappend(user.key, user.tags.json_path, "tag3")

    # Act
    await user.tags.load()

    # Assert
    assert len(user.tags) == 3
    assert "tag3" in user.tags
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert user.tags == actual_lst[0]


@pytest.mark.asyncio
async def test_base_redis_model__model_creation__check_redis_list_instance(
    real_redis_client,
):
    # Arrange & Act
    user = UserModel(tags=["tag1", "tag2"])

    # Assert
    from redis_pydantic.types.lst import RedisList

    assert isinstance(user.tags, RedisList)
    assert hasattr(user.tags, "redis_key")
    assert hasattr(user.tags, "field_path")
    assert hasattr(user.tags, "redis")
    assert hasattr(user.tags, "json_path")
    assert user.tags.redis_key == user.key
    assert user.tags.field_path == "tags"
    assert user.tags.json_path == "$.tags"
    assert user.tags.redis == real_redis_client
