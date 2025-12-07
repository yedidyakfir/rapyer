import pytest

from rapyer.types.dct import RedisDict
from rapyer.types.string import RedisStr
from tests.models.collection_types import DictModel


@pytest.mark.parametrize(
    "test_value",
    [
        {"key1": "value1", "key2": "value2"},
        {"name": "test", "type": "example"},
        {},
        {"single": "item"},
    ],
)
@pytest.mark.asyncio
async def test_redis_dict_model_creation_with_initial_value_and_set_load_sanity(
    test_value,
):
    # Arrange
    model = DictModel(data=test_value)

    assert isinstance(model.data, RedisDict)
    assert model.data.key == model.key
    assert model.data.field_path == ".data"
    assert model.data.json_path == "$.data"

    # Act - Save and test load operations
    await model.asave()

    # Assert - Load and verify
    model.data = await model.data.aload()
    assert dict(model.data) == test_value

    # Test load from fresh model
    fresh_model = DictModel()
    fresh_model.pk = model.pk
    fresh_model.data = await fresh_model.data.aload()
    assert dict(fresh_model.data) == test_value


@pytest.mark.asyncio
async def test_redis_dict_model_creation_with_dict_operations_sanity():
    # Arrange
    model = DictModel(data={"initial": "value"})

    # Assert model creation
    assert isinstance(model.data, RedisDict)
    assert model.data.json_path == "$.data"
    assert isinstance(model.data["initial"], RedisStr)

    # Act - Save and perform dict operations
    await model.asave()
    await model.data.aset_item("new_key", "new_value")
    await model.data.aupdate(extra="data")

    # Assert - Load and verify operations worked
    model.data = await model.data.aload()
    assert model.data["initial"] == "value"
    assert model.data["new_key"] == "new_value"
    assert model.data["extra"] == "data"
