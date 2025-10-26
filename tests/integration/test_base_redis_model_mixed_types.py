from typing import List, Dict, Any

import pytest
import pytest_asyncio
from pydantic import Field

from rapyer.base import AtomicRedisModel


class MixedTypesModel(AtomicRedisModel):
    str_list: List[str] = Field(default_factory=list)
    bytes_list: List[bytes] = Field(default_factory=list)
    int_list: List[int] = Field(default_factory=list)
    bool_list: List[bool] = Field(default_factory=list)
    mixed_list: List[Any] = Field(default_factory=list)
    str_dict: Dict[str, str] = Field(default_factory=dict)
    bytes_dict: Dict[str, bytes] = Field(default_factory=dict)
    int_dict: Dict[str, int] = Field(default_factory=dict)
    bool_dict: Dict[str, bool] = Field(default_factory=dict)
    mixed_dict: Dict[str, Any] = Field(default_factory=dict)


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    MixedTypesModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize("test_bytes", [b"hello", b"world", b"\x00\x01\x02"])
@pytest.mark.asyncio
async def test_bytes_list_append_functionality(test_bytes):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.bytes_list.aappend(test_bytes)

    # Assert
    assert test_bytes in model.bytes_list
    assert len(model.bytes_list) == 1

    original_data = list(model.bytes_list)
    fresh_model = MixedTypesModel()
    fresh_model.pk = model.pk
    await fresh_model.bytes_list.load()
    assert list(fresh_model.bytes_list) == original_data


@pytest.mark.parametrize("test_ints", [[1, 2, 3], [-5, 0, 42], [999, -999, 0]])
@pytest.mark.asyncio
async def test_int_list_extend_functionality(test_ints):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.int_list.aextend(test_ints)

    # Assert
    assert all(num in model.int_list for num in test_ints)
    assert len(model.int_list) == len(test_ints)

    original_data = list(model.int_list)
    fresh_model = MixedTypesModel()
    fresh_model.pk = model.pk
    await fresh_model.int_list.load()
    assert list(fresh_model.int_list) == original_data


@pytest.mark.parametrize(
    "bool_values", [[True, False], [True, True, False], [False, False, True, True]]
)
@pytest.mark.asyncio
async def test_bool_list_operations_functionality(bool_values):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.bool_list.aextend(bool_values)
    popped_value = await model.bool_list.apop()

    # Assert
    assert len(model.bool_list) == len(bool_values) - 1
    assert popped_value == bool_values[-1]

    original_data = list(model.bool_list)
    fresh_model = MixedTypesModel()
    fresh_model.pk = model.pk
    await fresh_model.bool_list.load()
    assert list(fresh_model.bool_list) == original_data


@pytest.mark.asyncio
async def test_mixed_list_with_different_types_functionality(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    mixed_values = ["string", 42, True, b"bytes", 3.14]
    await model.save()

    # Act
    await model.mixed_list.aextend(mixed_values)
    await model.mixed_list.ainsert(2, "inserted")

    # Assert
    assert len(model.mixed_list) == 6
    assert model.mixed_list[2] == "inserted"
    assert "string" in model.mixed_list
    assert 42 in model.mixed_list
    assert True in model.mixed_list

    await model.mixed_list.load()
    assert "string" in model.mixed_list
    assert 42 in model.mixed_list
    assert "inserted" in model.mixed_list
    assert True in model.mixed_list
    assert 3.14 in model.mixed_list


@pytest.mark.parametrize(
    "test_data",
    [
        {"key1": b"value1", "key2": b"value2"},
        {"binary": b"\x00\x01\x02", "text": b"hello world"},
    ],
)
@pytest.mark.asyncio
async def test_bytes_dict_operations_functionality(test_data):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.bytes_dict.aupdate(**test_data)

    # Assert
    assert len(model.bytes_dict) == len(test_data)
    for key, value in test_data.items():
        assert model.bytes_dict[key] == value

    original_data = dict(model.bytes_dict)
    fresh_model = MixedTypesModel()
    fresh_model.pk = model.pk
    await fresh_model.bytes_dict.load()
    assert dict(fresh_model.bytes_dict) == original_data


@pytest.mark.parametrize(
    "int_data",
    [{"count": 100, "age": 25}, {"negative": -50, "zero": 0, "positive": 999}],
)
@pytest.mark.asyncio
async def test_int_dict_operations_functionality(int_data):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.int_dict.aupdate(**int_data)
    await model.save()
    popped_value = await model.int_dict.apop(list(int_data.keys())[0])

    # Assert
    assert len(model.int_dict) == len(int_data) - 1
    assert popped_value == list(int_data.values())[0]

    original_data = dict(model.int_dict)
    fresh_model = MixedTypesModel()
    fresh_model.pk = model.pk
    await fresh_model.int_dict.load()
    assert dict(fresh_model.int_dict) == original_data


@pytest.mark.parametrize(
    "bool_data",
    [
        {"active": True, "deleted": False},
        {"flag1": True, "flag2": True, "flag3": False},
    ],
)
@pytest.mark.asyncio
async def test_bool_dict_operations_functionality(bool_data):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.bool_dict.aupdate(**bool_data)
    await model.save()

    # Assert
    assert len(model.bool_dict) == len(bool_data)
    for key, value in bool_data.items():
        assert model.bool_dict[key] == value
        assert isinstance(model.bool_dict[key], bool)

    original_data = dict(model.bool_dict)
    fresh_model = MixedTypesModel()
    fresh_model.pk = model.pk
    await fresh_model.bool_dict.load()
    assert dict(fresh_model.bool_dict) == original_data
    for key, value in fresh_model.bool_dict.items():
        assert isinstance(value, bool)


@pytest.mark.asyncio
async def test_mixed_dict_with_various_types_functionality(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    mixed_data = {
        "string_key": "string_value",
        "int_key": 42,
        "bool_key": True,
        "bytes_key": b"bytes_value",
        "float_key": 3.14,
    }
    await model.save()

    # Act
    await model.mixed_dict.aupdate(**mixed_data)
    await model.save()
    await model.mixed_dict.apop("int_key")

    # Assert
    assert len(model.mixed_dict) == 4
    assert "int_key" not in model.mixed_dict
    assert model.mixed_dict["string_key"] == "string_value"
    assert model.mixed_dict["bool_key"] is True

    await model.mixed_dict.load()
    assert model.mixed_dict["string_key"] == "string_value"
    assert model.mixed_dict["bool_key"] is True
    assert model.mixed_dict["bytes_key"] == b"bytes_value"
    assert model.mixed_dict["float_key"] == 3.14


@pytest.mark.asyncio
async def test_list_clear_with_mixed_types_functionality(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    mixed_values = ["string", 42, True, b"bytes"]
    await model.save()

    # Act
    await model.mixed_list.aextend(mixed_values)
    await model.mixed_list.aclear()

    # Assert
    assert len(model.mixed_list) == 0

    redis_data = await real_redis_client.json().get(model.key, "$.mixed_list")
    assert redis_data is None or redis_data == [] or redis_data[0] == []


@pytest.mark.asyncio
async def test_dict_clear_with_mixed_types_functionality(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    mixed_data = {"str": "value", "int": 42, "bool": True}
    await model.save()

    # Act
    await model.mixed_dict.aupdate(**mixed_data)
    await model.save()
    await model.mixed_dict.aclear()
    await model.save()

    # Assert
    assert len(model.mixed_dict) == 0


@pytest.mark.parametrize(
    ["list_type", "test_values"],
    [
        ["bytes_list", [b"test1", b"test2", b"test3"]],
        ["int_list", [10, 20, 30]],
        ["bool_list", [True, False, True]],
    ],
)
@pytest.mark.asyncio
async def test_list_persistence_across_instances_edge_case(list_type, test_values):
    # Arrange
    model1 = MixedTypesModel()
    target_list = getattr(model1, list_type)
    await model1.save()

    # Act
    await target_list.aextend(test_values)

    model2 = MixedTypesModel()
    model2.pk = model1.pk
    target_list2 = getattr(model2, list_type)
    await target_list2.load()

    # Assert
    assert list(target_list2) == test_values
    assert len(target_list2) == len(test_values)


@pytest.mark.parametrize(
    ["dict_type", "test_data"],
    [
        ["bytes_dict", {"key1": b"value1", "key2": b"value2"}],
        ["int_dict", {"num1": 100, "num2": 200}],
        ["bool_dict", {"flag1": True, "flag2": False}],
    ],
)
@pytest.mark.asyncio
async def test_dict_persistence_across_instances_edge_case(dict_type, test_data):
    # Arrange
    model1 = MixedTypesModel()
    target_dict = getattr(model1, dict_type)
    await model1.save()

    # Act
    await target_dict.aupdate(**test_data)
    await model1.save()

    model2 = MixedTypesModel()
    model2.pk = model1.pk
    target_dict2 = getattr(model2, dict_type)
    await target_dict2.load()

    # Assert
    assert dict(target_dict2) == test_data
    assert len(target_dict2) == len(test_data)


@pytest.mark.asyncio
async def test_bytes_list_with_special_characters_edge_case(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    special_bytes = [b"\x00\x01\x02\x03", b"\xff\xfe\xfd", b""]
    await model.save()

    # Act
    await model.bytes_list.aextend(special_bytes)

    # Assert
    assert len(model.bytes_list) == 3
    assert all(b in model.bytes_list for b in special_bytes)

    original_data = list(model.bytes_list)
    fresh_model = MixedTypesModel()
    fresh_model.pk = model.pk
    await fresh_model.bytes_list.load()
    assert list(fresh_model.bytes_list) == original_data


@pytest.mark.asyncio
async def test_mixed_operations_on_same_model_functionality(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.str_list.aappend("string")
    await model.int_list.aappend(42)
    await model.bool_dict.aset_item("active", True)
    await model.mixed_dict.aset_item("complex", {"nested": "data"})
    await model.save()

    # Assert
    assert "string" in model.str_list
    assert 42 in model.int_list
    assert model.bool_dict["active"] is True
    assert model.mixed_dict["complex"] == {"nested": "data"}

    original_str_list = list(model.str_list)
    original_int_list = list(model.int_list)
    original_bool_dict = dict(model.bool_dict)
    original_mixed_dict = dict(model.mixed_dict)

    fresh_model = MixedTypesModel()
    fresh_model.pk = model.pk
    await fresh_model.str_list.load()
    await fresh_model.int_list.load()
    await fresh_model.bool_dict.load()
    await fresh_model.mixed_dict.load()

    assert list(fresh_model.str_list) == original_str_list
    assert list(fresh_model.int_list) == original_int_list
    assert dict(fresh_model.bool_dict) == original_bool_dict
    assert dict(fresh_model.mixed_dict) == original_mixed_dict
