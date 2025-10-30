import pytest

from rapyer.types.dct import RedisDict
from rapyer.types.integer import RedisInt
from rapyer.types.lst import RedisList
from rapyer.types.string import RedisStr
from tests.models.collection_types import (
    SimpleListModel,
    SimpleIntListModel,
    SimpleDictModel,
)
from tests.models.unit_types import SimpleIntDictModel


@pytest.mark.parametrize(
    "initial_items,new_item", [(["hello"], "world"), ([], "first"), (["a", "b"], "c")]
)
def test_redis_list_append_operation_sanity(initial_items, new_item):
    # Arrange
    model = SimpleListModel(items=initial_items)

    # Act - Test append operation
    model.items.append(new_item)

    # Assert
    assert isinstance(model.items, RedisList)
    assert len(model.items) == len(initial_items) + 1
    assert isinstance(model.items[-1], RedisStr)
    assert str(model.items[-1]) == new_item
    assert model.items[-1].key == model.key


@pytest.mark.parametrize(
    "initial_items,extend_items",
    [
        (["hello"], ["world", "test"]),
        ([], ["first", "second"]),
        (["a"], ["b", "c", "d"]),
    ],
)
def test_redis_list_extend_operation_sanity(initial_items, extend_items):
    # Arrange
    model = SimpleListModel(items=initial_items)

    # Act - Test extend operation
    model.items.extend(extend_items)

    # Assert
    assert isinstance(model.items, RedisList)
    assert len(model.items) == len(initial_items) + len(extend_items)

    for i, item in enumerate(extend_items):
        idx = len(initial_items) + i
        assert isinstance(model.items[idx], RedisStr)
        assert str(model.items[idx]) == item
        assert model.items[idx].key == model.key


@pytest.mark.parametrize(
    "initial_items,index,new_item",
    [
        (["hello", "world"], 1, "new"),
        (["a", "b", "c"], 0, "start"),
        (["x"], 0, "replace"),
    ],
)
def test_redis_list_setitem_operation_sanity(initial_items, index, new_item):
    # Arrange
    model = SimpleListModel(items=initial_items)

    # Act - Test setitem operation
    model.items[index] = new_item

    # Assert
    assert isinstance(model.items, RedisList)
    assert isinstance(model.items[index], RedisStr)
    assert str(model.items[index]) == new_item
    assert model.items[index].key == model.key


@pytest.mark.parametrize(
    "initial_numbers,increment_ops",
    [([1, 2, 3], [(0, 5), (1, 10)]), ([0], [(0, 1)]), ([10, 20], [(1, -5)])],
)
def test_redis_int_list_arithmetic_operations_sanity(initial_numbers, increment_ops):
    # Arrange
    model = SimpleIntListModel(numbers=initial_numbers)

    # Act & Assert
    for index, increment in increment_ops:
        original_value = int(model.numbers[index])
        result = model.numbers[index] + increment
        assert result == original_value + increment
        assert isinstance(model.numbers[index], RedisInt)


@pytest.mark.parametrize(
    "initial_data,new_key,new_value",
    [
        ({"key1": "value1"}, "key2", "value2"),
        ({}, "first", "value"),
        ({"existing": "old"}, "new", "fresh"),
    ],
)
def test_redis_dict_setitem_operation_sanity(initial_data, new_key, new_value):
    # Arrange
    model = SimpleDictModel(data=initial_data)

    # Act - Test setitem operation
    model.data[new_key] = new_value

    # Assert
    assert isinstance(model.data, RedisDict)
    assert new_key in model.data
    assert isinstance(model.data[new_key], RedisStr)
    assert str(model.data[new_key]) == new_value
    assert model.data[new_key].key == model.key
    assert model.data[new_key].field_name == f"data.{new_key}"


@pytest.mark.parametrize(
    "initial_data,update_data",
    [
        ({"key1": "value1"}, {"key2": "value2", "key3": "value3"}),
        ({}, {"first": "value", "second": "another"}),
        ({"existing": "old"}, {"existing": "updated", "new": "value"}),
    ],
)
def test_redis_dict_update_operation_sanity(initial_data, update_data):
    # Arrange
    model = SimpleDictModel(data=initial_data)

    # Act - Test update operation using |= operator
    model.data |= update_data

    # Assert
    assert isinstance(model.data, RedisDict)

    for key, value in update_data.items():
        assert key in model.data
        assert isinstance(model.data[key], RedisStr)
        assert str(model.data[key]) == value
        assert model.data[key].key == model.key


@pytest.mark.parametrize(
    "initial_counts,key,increment",
    [
        ({"count1": 10}, "count1", 5),
        ({"total": 0}, "total", 1),
        ({"score": 100}, "score", -10),
    ],
)
def test_redis_int_dict_arithmetic_operations_sanity(initial_counts, key, increment):
    # Arrange
    model = SimpleIntDictModel(counts=initial_counts)

    # Act & Assert
    original_value = int(model.counts[key])
    result = model.counts[key] + increment
    assert result == original_value + increment
    assert isinstance(model.counts[key], RedisInt)


def test_redis_list_clear_operation_sanity():
    # Arrange
    model = SimpleListModel(items=["hello", "world", "test"])

    # Act
    model.items.clear()

    # Assert
    assert isinstance(model.items, RedisList)
    assert len(model.items) == 0


def test_redis_dict_clear_operation_sanity():
    # Arrange
    model = SimpleDictModel(data={"key1": "value1", "key2": "value2"})

    # Act
    model.data.clear()

    # Assert
    assert isinstance(model.data, RedisDict)
    assert len(model.data) == 0


def test_redis_list_pop_operation_sanity():
    # Arrange
    model = SimpleListModel(items=["hello", "world", "test"])

    # Act
    popped = model.items.pop()

    # Assert
    assert isinstance(model.items, RedisList)
    assert len(model.items) == 2
    assert popped == "test"


def test_redis_dict_pop_operation_sanity():
    # Arrange
    model = SimpleDictModel(data={"key1": "value1", "key2": "value2"})

    # Act
    popped = model.data.pop("key1")

    # Assert
    assert isinstance(model.data, RedisDict)
    assert len(model.data) == 1
    assert "key1" not in model.data
    assert popped == "value1"


def test_redis_list_insert_operation_sanity():
    # Arrange
    model = SimpleListModel(items=["hello", "world"])

    # Act
    model.items.insert(1, "middle")

    # Assert
    assert isinstance(model.items, RedisList)
    assert len(model.items) == 3
    assert isinstance(model.items[1], RedisStr)
    assert str(model.items[1]) == "middle"
    assert model.items[1].key == model.key
