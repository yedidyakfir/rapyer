import pytest
import pytest_asyncio
from pydantic import Field

from redis_pydantic.base import BaseRedisModel


class IntDictModel(BaseRedisModel):
    metadata: dict[str, int] = Field(default_factory=dict)


class StrDictModel(BaseRedisModel):
    metadata: dict[str, str] = Field(default_factory=dict)


class DictDictModel(BaseRedisModel):
    metadata: dict[str, dict[str, str]] = Field(default_factory=dict)


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    IntDictModel.Meta.redis = redis_client
    StrDictModel.Meta.redis = redis_client
    DictDictModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize("model_class,test_value", [
    [IntDictModel, 42],
    [StrDictModel, "test_string"],
    [DictDictModel, {"nested_key": "nested_value"}],
])
@pytest.mark.asyncio
async def test_redis_dict_setitem_type_checking_sanity(real_redis_client, model_class, test_value):
    # Arrange
    model = model_class()
    await model.save()

    # Act
    model.metadata["test_key"] = test_value

    # Assert
    from redis_pydantic.types.integer import RedisInt
    from redis_pydantic.types.string import RedisStr
    from redis_pydantic.types.dct import RedisDict

    if isinstance(test_value, int):
        assert isinstance(model.metadata["test_key"], RedisInt)
    elif isinstance(test_value, str):
        assert isinstance(model.metadata["test_key"], RedisStr)
    elif isinstance(test_value, dict):
        assert isinstance(model.metadata["test_key"], RedisDict)


@pytest.mark.parametrize("key,test_value", [
    ["count", 100],
    ["score", 200],
    ["level", 300],
])
@pytest.mark.asyncio
async def test_redis_dict_setitem_int_operations_sanity(real_redis_client, key, test_value):
    # Arrange
    model = IntDictModel()
    await model.save()
    
    # Act
    model.metadata[key] = test_value
    await model.metadata[key].set(test_value + 50)

    # Assert
    fresh_model = IntDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    # After loading, values are regular Python types, not Redis types
    assert fresh_model.metadata[key] == test_value + 50


@pytest.mark.parametrize("key,test_value", [
    ["name", "hello"],
    ["title", "world"],
    ["description", "test"],
])
@pytest.mark.asyncio
async def test_redis_dict_setitem_str_operations_sanity(real_redis_client, key, test_value):
    # Arrange
    model = StrDictModel()
    await model.save()
    
    # Act
    model.metadata[key] = test_value
    await model.metadata[key].set(test_value + "_modified")

    # Assert
    fresh_model = StrDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    # After loading, values are regular Python types, not Redis types
    assert fresh_model.metadata[key] == test_value + "_modified"


@pytest.mark.parametrize("key,test_value", [
    ["config", {"setting1": "value1"}],
    ["options", {"setting2": "value2"}],
    ["preferences", {"setting3": "value3"}],
])
@pytest.mark.asyncio
async def test_redis_dict_setitem_nested_dict_operations_sanity(real_redis_client, key, test_value):
    # Arrange
    model = DictDictModel()
    await model.save()
    
    # Act
    model.metadata[key] = test_value
    await model.save()  # Save current state to Redis before update
    await model.metadata[key].aupdate(**{"new_setting": "new_value"})

    # Assert
    fresh_model = DictDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    # After loading, values are regular Python types, not Redis types
    expected_dict = {**test_value, "new_setting": "new_value"}
    assert fresh_model.metadata[key] == expected_dict


@pytest.mark.asyncio
async def test_redis_dict_setitem_int_arithmetic_operations_sanity(real_redis_client):
    # Arrange
    model = IntDictModel()
    await model.save()
    
    # Act
    model.metadata["number"] = 50

    # Assert
    assert model.metadata["number"] + 10 == 60
    assert model.metadata["number"] - 5 == 45
    assert model.metadata["number"] * 2 == 100
    assert model.metadata["number"] == 50


@pytest.mark.asyncio
async def test_redis_dict_setitem_str_operations_edge_case(real_redis_client):
    # Arrange
    model = StrDictModel()
    await model.save()
    
    # Act
    model.metadata["text"] = "test"

    # Assert
    assert model.metadata["text"] + "_suffix" == "test_suffix"
    assert model.metadata["text"].upper() == "TEST"
    assert len(model.metadata["text"]) == 4


@pytest.mark.asyncio
async def test_redis_dict_setitem_nested_dict_key_access_edge_case(real_redis_client):
    # Arrange
    model = DictDictModel()
    await model.save()
    
    # Act
    model.metadata["config"] = {"key1": "value1", "key2": "value2"}

    # Assert
    assert model.metadata["config"]["key1"] == "value1"
    assert model.metadata["config"]["key2"] == "value2"
    assert len(model.metadata["config"]) == 2


@pytest.mark.asyncio
async def test_redis_dict_setitem_redis_field_paths_sanity(real_redis_client):
    # Arrange
    model = IntDictModel()
    await model.save()
    
    # Act
    model.metadata["test_key"] = 42

    # Assert
    assert model.metadata["test_key"].redis_key == model.key
    assert model.metadata["test_key"].field_path == "metadata.test_key"
    assert model.metadata["test_key"].json_path == "$.metadata.test_key"


@pytest.mark.asyncio
async def test_redis_dict_setitem_multiple_keys_sanity(real_redis_client):
    # Arrange
    model = IntDictModel()
    await model.save()
    
    # Act
    model.metadata["key1"] = 10
    model.metadata["key2"] = 20
    model.metadata["key3"] = 30

    # Assert
    assert model.metadata["key1"] == 10
    assert model.metadata["key2"] == 20
    assert model.metadata["key3"] == 30
    assert len(model.metadata) == 3


@pytest.mark.asyncio
async def test_redis_dict_setitem_persistence_across_instances_edge_case(real_redis_client):
    # Arrange
    model1 = IntDictModel()
    await model1.save()
    
    # Act
    model1.metadata["test_key"] = 99
    await model1.metadata["test_key"].set(99)
    
    # Assert
    model2 = IntDictModel()
    model2.pk = model1.pk
    await model2.metadata.load()
    # After loading, values are regular Python types, not Redis types
    assert model2.metadata["test_key"] == 99


@pytest.mark.asyncio
async def test_redis_dict_setitem_with_existing_redis_operations_sanity(real_redis_client):
    # Arrange
    model = StrDictModel()
    model.metadata = {"existing_key": "existing_value"}
    await model.save()
    
    # Act - use setitem to add a new key
    model.metadata["new_key"] = "new_value"
    await model.metadata["new_key"].set("updated_value")
    
    # Also use setitem to convert existing key to Redis type
    model.metadata["existing_key"] = "existing_value"  # Convert to Redis type via setitem
    await model.metadata["existing_key"].set("updated_existing")

    # Assert
    fresh_model = StrDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    assert fresh_model.metadata["new_key"] == "updated_value"
    assert fresh_model.metadata["existing_key"] == "updated_existing"


@pytest.mark.asyncio
async def test_redis_dict_setitem_overwrite_existing_key_sanity(real_redis_client):
    # Arrange
    model = IntDictModel()
    model.metadata = {"key1": 10}
    await model.save()
    
    # Act - overwrite existing key with setitem
    model.metadata["key1"] = 99
    await model.metadata["key1"].set(150)

    # Assert
    fresh_model = IntDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    assert fresh_model.metadata["key1"] == 150


@pytest.mark.asyncio
async def test_redis_dict_setitem_mixed_operations_sanity(real_redis_client):
    # Arrange
    model = StrDictModel()
    await model.save()
    
    # Act - mix setitem with aset_item and aupdate
    model.metadata["key1"] = "value1"  # setitem
    await model.metadata.aset_item("key2", "value2")  # aset_item
    await model.metadata.aupdate(key3="value3")  # aupdate
    
    # Use Redis operations on setitem-created value
    await model.metadata["key1"].set("modified_value1")

    # Assert
    fresh_model = StrDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    assert fresh_model.metadata["key1"] == "modified_value1"
    assert fresh_model.metadata["key2"] == "value2"
    assert fresh_model.metadata["key3"] == "value3"
    assert len(fresh_model.metadata) == 3