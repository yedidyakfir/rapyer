import pytest

from rapyer.types.lst import RedisList
from rapyer.types.string import RedisStr
from tests.models.collection_types import ListModel


@pytest.mark.parametrize(
    "test_value",
    [
        ["item1", "item2", "item3"],
        ["hello", "world"],
        ["single"],
    ],
)
@pytest.mark.asyncio
async def test_redis_list_model_creation_with_initial_value_and_set_load_sanity(
    test_value,
):
    # Arrange
    model = ListModel(items=test_value)

    # Assert model creation
    assert isinstance(model.items, RedisList)
    assert model.items.key == model.key
    assert model.items.field_path == ".items"
    assert model.items.json_path == "$.items"
    for i in range(len(test_value)):
        assert isinstance(model.items[i], RedisStr)
        assert model.items[i].key == model.key
        assert model.items[i].json_path == f"$.items[{i}]"

    # Act - Save and test load operations
    await model.save()

    # Assert - Load and verify
    loaded_value = await model.items.load()
    assert loaded_value == test_value

    # Test load from a fresh model
    fresh_model = ListModel()
    fresh_model.pk = model.pk
    fresh_loaded_value = await fresh_model.items.load()
    assert fresh_loaded_value == test_value


@pytest.mark.asyncio
async def test_redis_list_model_creation_with_list_operations_sanity():
    # Arrange
    model = ListModel(items=["initial"])

    # Assert model creation
    assert isinstance(model.items, RedisList)
    assert model.items.json_path == "$.items"
    assert isinstance(model.items[0], RedisStr)
    assert model.items[0].json_path == "$.items[0]"

    # Act - Save and perform list operations
    await model.save()
    await model.items.aappend("new_item")
    await model.items.aextend(["item2", "item3"])

    # Assert - Load and verify operations worked
    loaded_items = await model.items.load()
    assert "initial" in loaded_items
    assert "new_item" in loaded_items
    assert "item2" in loaded_items
    assert "item3" in loaded_items
