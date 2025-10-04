import pytest
import pytest_asyncio

import redis_pydantic
from redis_pydantic.base import BaseRedisModel
from redis_pydantic.types import ALL_TYPES


class UserModel(BaseRedisModel):
    metadata: dict[str, str] = {}

    class Meta:
        redis = None  # Will be set in fixture
        redis_type = ALL_TYPES


@pytest_asyncio.fixture
async def real_redis_client():
    redis = await redis_pydantic.BaseRedisModel.Meta.redis.from_url(
        "redis://localhost:6371/0"
    )
    UserModel.Meta.redis = redis
    await redis.flushall()
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest.mark.asyncio
async def test_redis_dict__setitem__check_local_consistency(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    user.metadata["key2"] = "value2"
    await user.save()  # Sync with Redis

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert user.metadata == actual_dict[0]


@pytest.mark.asyncio
async def test_redis_dict__delitem__check_local_consistency(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1", "key2": "value2"})
    await user.save()

    # Act
    del user.metadata["key1"]
    await user.save()  # Sync with Redis

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert user.metadata == actual_dict[0]


@pytest.mark.asyncio
async def test_redis_dict__update__check_local_consistency(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    user.metadata.update({"key2": "value2", "key3": "value3"})
    await user.save()  # Sync with Redis

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert user.metadata == actual_dict[0]


@pytest.mark.asyncio
async def test_redis_dict__clear__check_local_consistency(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1", "key2": "value2"})
    await user.save()

    # Act
    user.metadata.clear()
    await user.save()  # Sync with Redis

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert len(user.metadata) == 0
    assert user.metadata == actual_dict[0]


@pytest.mark.asyncio
async def test_redis_dict__load__check_redis_load(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()
    await real_redis_client.json().set(
        user.key, f"{user.metadata.json_path}.key2", "value2"
    )

    # Act
    await user.metadata.load()

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert user.metadata == actual_dict[0]


@pytest.mark.asyncio
async def test_redis_dict__pop__check_redis_pop(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1", "key2": "value2"})
    await user.save()

    # Act
    popped_value = await user.metadata.pop("key1")

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert user.metadata == actual_dict[0]
    assert popped_value == "value1"
    assert "key1" not in user.metadata
    assert len(user.metadata) == 1


@pytest.mark.asyncio
async def test_redis_dict__pop_with_default__check_default_return(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    result = await user.metadata.pop("nonexistent", "default_value")

    # Assert
    assert result == "default_value"
    assert len(user.metadata) == 1


@pytest.mark.asyncio
async def test_redis_dict__pop_no_default__check_key_error(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act & Assert
    with pytest.raises(KeyError):
        await user.metadata.pop("nonexistent")


@pytest.mark.asyncio
async def test_redis_dict__popitem__check_redis_popitem(real_redis_client):
    # Arrange
    original_dict = {"key1": "value1", "key2": "value2"}
    user = UserModel(metadata=original_dict)
    await user.save()

    # Act
    popped_value = await user.metadata.popitem()

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert user.metadata == actual_dict[0]
    assert popped_value in original_dict.values()
    assert len(user.metadata) == 1


@pytest.mark.asyncio
async def test_redis_dict__update_with_dict_arg__check_local_consistency(
    real_redis_client,
):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    user.metadata.update({"key2": "value2", "key3": "value3"})
    await user.save()  # Sync with Redis

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert user.metadata == actual_dict[0]
    assert len(user.metadata) == 3


@pytest.mark.asyncio
async def test_redis_dict__update_with_iterable_arg__check_local_consistency(
    real_redis_client,
):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    user.metadata.update([("key2", "value2"), ("key3", "value3")])
    await user.save()  # Sync with Redis

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert user.metadata == actual_dict[0]
    assert len(user.metadata) == 3


@pytest.mark.asyncio
async def test_redis_dict__update_with_kwargs__check_local_consistency(
    real_redis_client,
):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    user.metadata.update(key2="value2", key3="value3")
    await user.save()  # Sync with Redis

    # Assert
    actual_dict = await real_redis_client.json().get(user.key, user.metadata.json_path)
    assert user.metadata == actual_dict[0]
    assert len(user.metadata) == 3


@pytest.mark.asyncio
async def test_redis_dict__clone__check_clone_functionality(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1", "key2": "value2"})

    # Act
    cloned_dict = user.metadata.clone()

    # Assert
    assert isinstance(cloned_dict, dict)
    assert not isinstance(
        cloned_dict, type(user.metadata)
    )  # Should be regular dict, not RedisDict
    assert cloned_dict == {"key1": "value1", "key2": "value2"}
    assert cloned_dict == user.metadata
    # Verify it's a copy, not the same object
    cloned_dict["key3"] = "value3"
    assert "key3" not in user.metadata


@pytest.mark.asyncio
async def test_redis_dict__popitem_empty_dict__check_key_error(real_redis_client):
    # Arrange
    user = UserModel(metadata={})
    await user.save()

    # Act & Assert
    with pytest.raises(KeyError, match="popitem\\(\\): dictionary is empty"):
        await user.metadata.popitem()


@pytest.mark.asyncio
async def test_redis_dict__model_creation__check_redis_dict_instance(real_redis_client):
    # Arrange & Act
    user = UserModel(metadata={"key1": "value1"})

    # Assert
    from redis_pydantic.types.dct import RedisDict

    assert isinstance(user.metadata, RedisDict)
    assert hasattr(user.metadata, "redis_key")
    assert hasattr(user.metadata, "field_path")
    assert hasattr(user.metadata, "redis")
    assert hasattr(user.metadata, "json_path")
    assert user.metadata.redis_key == user.key
    assert user.metadata.field_path == "metadata"
    assert user.metadata.json_path == "$.metadata"
    assert user.metadata.redis == real_redis_client
