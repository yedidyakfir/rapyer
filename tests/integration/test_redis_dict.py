import pytest
import pytest_asyncio

from redis_pydantic.base import BaseRedisModel


class UserModel(BaseRedisModel):
    metadata: dict[str, str] = {}


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    UserModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_redis_dict__setitem__check_local_consistency(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    await user.metadata.aset_item("key2", "value2")
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = UserModel()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata


@pytest.mark.asyncio
async def test_redis_dict__delitem__check_local_consistency(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1", "key2": "value2"})
    await user.save()

    # Act
    await user.metadata.adel_item("key1")
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = UserModel()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata


@pytest.mark.asyncio
async def test_redis_dict__update__check_local_consistency(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    await user.metadata.aupdate(**{"key2": "value2", "key3": "value3"})
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = UserModel()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata


@pytest.mark.asyncio
async def test_redis_dict__clear__check_local_consistency(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1", "key2": "value2"})
    await user.save()

    # Act
    await user.metadata.aclear()
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = UserModel()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert len(user.metadata) == 0
    assert user.metadata == fresh_user.metadata


@pytest.mark.asyncio
async def test_redis_dict__load__check_redis_load(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()
    # Use another user instance to set a value and verify load works
    other_user = UserModel()
    other_user.pk = user.pk
    await other_user.metadata.load()
    await other_user.metadata.aset_item("key2", "value2")

    # Act
    await user.metadata.load()

    # Assert
    fresh_user = UserModel()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
    assert "key2" in user.metadata
    assert user.metadata["key2"] == "value2"


@pytest.mark.asyncio
async def test_redis_dict__pop__check_redis_pop(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1", "key2": "value2"})
    await user.save()

    # Act
    popped_value = await user.metadata.apop("key1")

    # Assert
    fresh_user = UserModel()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
    assert popped_value == "value1"
    assert "key1" not in user.metadata
    assert len(user.metadata) == 1


@pytest.mark.asyncio
async def test_redis_dict__pop_with_default__check_default_return(real_redis_client):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    result = await user.metadata.apop("nonexistent", "default_value")

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
        await user.metadata.apop("nonexistent")


@pytest.mark.asyncio
async def test_redis_dict__popitem__check_redis_popitem(real_redis_client):
    # Arrange
    original_dict = {"key1": "value1", "key2": "value2"}
    user = UserModel(metadata=original_dict)
    await user.save()

    # Act
    popped_value = await user.metadata.apopitem()

    # Assert
    fresh_user = UserModel()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
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
    await user.metadata.aupdate(**{"key2": "value2", "key3": "value3"})
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = UserModel()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
    assert len(user.metadata) == 3


@pytest.mark.asyncio
async def test_redis_dict__update_with_kwargs__check_local_consistency(
    real_redis_client,
):
    # Arrange
    user = UserModel(metadata={"key1": "value1"})
    await user.save()

    # Act
    await user.metadata.aupdate(key2="value2", key3="value3")
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = UserModel()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
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
        await user.metadata.apopitem()


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
