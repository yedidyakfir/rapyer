from typing import List, Dict, Any

import pytest
import pytest_asyncio
from pydantic import Field

from redis_pydantic.base import BaseRedisModel
from redis_pydantic.types import ALL_TYPES


class MixedTypesModel(BaseRedisModel):
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

    class Meta:
        redis = None
        redis_type = ALL_TYPES


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    MixedTypesModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize("test_bytes", [b"hello", b"world", b"\x00\x01\x02"])
@pytest.mark.asyncio
async def test_bytes_list_append_functionality(real_redis_client, test_bytes):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.bytes_list.append(test_bytes)

    # Assert
    assert test_bytes in model.bytes_list
    assert len(model.bytes_list) == 1

    redis_data = await real_redis_client.json().get(model.key, "$.bytes_list")
    assert redis_data is not None
    assert test_bytes in redis_data


@pytest.mark.parametrize("test_ints", [[1, 2, 3], [-5, 0, 42], [999, -999, 0]])
@pytest.mark.asyncio
async def test_int_list_extend_functionality(real_redis_client, test_ints):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.int_list.extend(test_ints)

    # Assert
    assert all(num in model.int_list for num in test_ints)
    assert len(model.int_list) == len(test_ints)

    redis_data = await real_redis_client.json().get(model.key, "$.int_list")
    assert redis_data is not None
    assert all(num in redis_data for num in test_ints)


@pytest.mark.parametrize(
    "bool_values", [[True, False], [True, True, False], [False, False, True, True]]
)
@pytest.mark.asyncio
async def test_bool_list_operations_functionality(real_redis_client, bool_values):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.bool_list.extend(bool_values)
    popped_value = await model.bool_list.pop()

    # Assert
    assert len(model.bool_list) == len(bool_values) - 1
    assert popped_value == bool_values[-1]

    redis_data = await real_redis_client.json().get(model.key, "$.bool_list")
    assert redis_data is not None
    assert len(redis_data) == len(bool_values) - 1


@pytest.mark.asyncio
async def test_mixed_list_with_different_types_functionality(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    mixed_values = ["string", 42, True, b"bytes", 3.14]
    await model.save()

    # Act
    await model.mixed_list.extend(mixed_values)
    await model.mixed_list.insert(2, "inserted")

    # Assert
    assert len(model.mixed_list) == 6
    assert model.mixed_list[2] == "inserted"
    assert "string" in model.mixed_list
    assert 42 in model.mixed_list
    assert True in model.mixed_list

    redis_data = await real_redis_client.json().get(model.key, "$.mixed_list")
    assert redis_data is not None
    assert len(redis_data) == 6


@pytest.mark.parametrize(
    "test_data",
    [
        {"key1": b"value1", "key2": b"value2"},
        {"binary": b"\x00\x01\x02", "text": b"hello world"},
    ],
)
@pytest.mark.asyncio
async def test_bytes_dict_operations_functionality(real_redis_client, test_data):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    model.bytes_dict.update(test_data)
    await model.save()

    # Assert
    assert len(model.bytes_dict) == len(test_data)
    for key, value in test_data.items():
        assert model.bytes_dict[key] == value

    redis_data = await real_redis_client.json().get(
        model.key, model.bytes_dict.json_path
    )
    assert redis_data is not None


@pytest.mark.parametrize(
    "int_data",
    [{"count": 100, "age": 25}, {"negative": -50, "zero": 0, "positive": 999}],
)
@pytest.mark.asyncio
async def test_int_dict_operations_functionality(real_redis_client, int_data):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    model.int_dict.update(int_data)
    await model.save()
    popped_value = await model.int_dict.pop(list(int_data.keys())[0])

    # Assert
    assert len(model.int_dict) == len(int_data) - 1
    assert popped_value == list(int_data.values())[0]

    redis_data = await real_redis_client.json().get(model.key, model.int_dict.json_path)
    assert redis_data is not None


@pytest.mark.parametrize(
    "bool_data",
    [
        {"active": True, "deleted": False},
        {"flag1": True, "flag2": True, "flag3": False},
    ],
)
@pytest.mark.asyncio
async def test_bool_dict_operations_functionality(real_redis_client, bool_data):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    model.bool_dict.update(bool_data)
    await model.save()

    # Assert
    assert len(model.bool_dict) == len(bool_data)
    for key, value in bool_data.items():
        assert model.bool_dict[key] == value
        assert isinstance(model.bool_dict[key], bool)

    redis_data = await real_redis_client.json().get(
        model.key, model.bool_dict.json_path
    )
    assert redis_data is not None


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
    model.mixed_dict.update(mixed_data)
    await model.save()
    await model.mixed_dict.pop("int_key")

    # Assert
    assert len(model.mixed_dict) == 4
    assert "int_key" not in model.mixed_dict
    assert model.mixed_dict["string_key"] == "string_value"
    assert model.mixed_dict["bool_key"] is True

    redis_data = await real_redis_client.json().get(
        model.key, model.mixed_dict.json_path
    )
    assert redis_data is not None
    assert len(redis_data) == 4


@pytest.mark.asyncio
async def test_list_clear_with_mixed_types_functionality(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    mixed_values = ["string", 42, True, b"bytes"]

    # Act
    await model.mixed_list.extend(mixed_values)
    await model.mixed_list.clear()

    # Assert
    assert len(model.mixed_list) == 0

    redis_data = await real_redis_client.json().get(model.key, "$.mixed_list")
    assert redis_data is None or len(redis_data) == 0


@pytest.mark.asyncio
async def test_dict_clear_with_mixed_types_functionality(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    mixed_data = {"str": "value", "int": 42, "bool": True}
    await model.save()

    # Act
    model.mixed_dict.update(mixed_data)
    await model.save()
    model.mixed_dict.clear()
    await model.save()

    # Assert
    assert len(model.mixed_dict) == 0

    redis_data = await real_redis_client.json().get(
        model.key, model.mixed_dict.json_path
    )
    assert len(model.mixed_dict) == 0


@pytest.mark.parametrize(
    "list_type,test_values",
    [
        ("bytes_list", [b"test1", b"test2", b"test3"]),
        ("int_list", [10, 20, 30]),
        ("bool_list", [True, False, True]),
    ],
)
@pytest.mark.asyncio
async def test_list_persistence_across_instances_edge_case(
    real_redis_client, list_type, test_values
):
    # Arrange
    model1 = MixedTypesModel()
    target_list = getattr(model1, list_type)
    await model1.save()

    # Act
    await target_list.extend(test_values)

    model2 = MixedTypesModel()
    model2.pk = model1.pk
    target_list2 = getattr(model2, list_type)
    await target_list2.load()

    # Assert
    assert list(target_list2) == test_values
    assert len(target_list2) == len(test_values)


@pytest.mark.parametrize(
    "dict_type,test_data",
    [
        ("bytes_dict", {"key1": b"value1", "key2": b"value2"}),
        ("int_dict", {"num1": 100, "num2": 200}),
        ("bool_dict", {"flag1": True, "flag2": False}),
    ],
)
@pytest.mark.asyncio
async def test_dict_persistence_across_instances_edge_case(
    real_redis_client, dict_type, test_data
):
    # Arrange
    model1 = MixedTypesModel()
    target_dict = getattr(model1, dict_type)
    await model1.save()

    # Act
    target_dict.update(test_data)
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
    await model.bytes_list.extend(special_bytes)

    # Assert
    assert len(model.bytes_list) == 3
    assert all(b in model.bytes_list for b in special_bytes)

    redis_data = await real_redis_client.json().get(model.key, "$.bytes_list")
    assert redis_data is not None
    assert len(redis_data) == 3


@pytest.mark.asyncio
async def test_mixed_operations_on_same_model_functionality(real_redis_client):
    # Arrange
    model = MixedTypesModel()
    await model.save()

    # Act
    await model.str_list.append("string")
    await model.int_list.append(42)
    model.bool_dict["active"] = True
    model.mixed_dict["complex"] = {"nested": "data"}
    await model.save()

    # Assert
    assert "string" in model.str_list
    assert 42 in model.int_list
    assert model.bool_dict["active"] is True
    assert model.mixed_dict["complex"] == {"nested": "data"}

    str_redis_data = await real_redis_client.json().get(model.key, "$.str_list")
    int_redis_data = await real_redis_client.json().get(model.key, "$.int_list")
    bool_redis_data = await real_redis_client.json().get(
        model.key, model.bool_dict.json_path
    )
    mixed_redis_data = await real_redis_client.json().get(
        model.key, model.mixed_dict.json_path
    )

    assert str_redis_data is not None
    assert int_redis_data is not None
    assert bool_redis_data is not None
    assert mixed_redis_data is not None
