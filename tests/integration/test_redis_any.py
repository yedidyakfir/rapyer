from datetime import datetime, date
from decimal import Decimal
from typing import Any, List, Dict

import pytest
import pytest_asyncio
from pydantic import Field

from rapyer.base import AtomicRedisModel


class AnyModel(AtomicRedisModel):
    simple_any: Any = "default"
    list_any: List[Any] = Field(default_factory=list)
    dict_any: Dict[str, Any] = Field(default_factory=dict)


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    AnyModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


test_data_args = [
    "hello",
    42,
    3.14,
    True,
    False,
    [1, 2, 3],
    {"key": "value"},
    None,
    datetime(2023, 1, 1, 12, 0, 0),
    date(2023, 1, 1),
    Decimal("123.45"),
    {"nested": {"deep": [1, 2, {"very": "deep"}]}},
]


@pytest.mark.parametrize("test_data", test_data_args)
@pytest.mark.asyncio
async def test_redis_any_set_functionality_sanity(test_data):
    # Arrange
    model = AnyModel()
    await model.save()

    # Act
    await model.simple_any.set(test_data)

    # Assert
    fresh_model = AnyModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.simple_any.load()
    assert loaded_value == test_data
    assert type(loaded_value) == type(test_data)


@pytest.mark.parametrize(
    "test_data",
    test_data_args,
)
@pytest.mark.asyncio
async def test_redis_any_load_functionality_sanity(test_data):
    # Arrange
    model = AnyModel()
    await model.save()
    await model.simple_any.set(test_data)

    # Act
    fresh_model = AnyModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.simple_any.load()

    # Assert
    assert loaded_value == test_data
    assert type(loaded_value) == type(test_data)


@pytest.mark.asyncio
async def test_redis_any_load_with_no_redis_data_edge_case():
    # Arrange
    model = AnyModel()

    # Act
    loaded_value = await model.simple_any.load()

    # Assert
    assert loaded_value is None


@pytest.mark.parametrize(
    "list_data",
    [
        [1, "two", 3.0, True, None],
        [{"a": 1}, [1, 2], "string", 42],
        [],
        [datetime(2023, 1, 1), date(2023, 1, 1), Decimal("10.5")],
        [{"nested": {"list": [1, 2, 3]}}, "mixed", 123],
    ],
)
@pytest.mark.asyncio
async def test_redis_list_any_set_functionality_sanity(list_data):
    # Arrange
    model = AnyModel()
    await model.save()

    # Act
    # Set to empty list first, then extend if there's data
    await model.list_any.client.json().set(
        model.list_any.redis_key, model.list_any.json_path, []
    )
    if list_data:
        await model.list_any.aextend(list_data)

    # Assert
    fresh_model = AnyModel()
    fresh_model.pk = model.pk
    await fresh_model.list_any.load()
    loaded_value = list(fresh_model.list_any)
    assert loaded_value == list_data
    assert len(loaded_value) == len(list_data)
    for i, item in enumerate(loaded_value):
        assert item == list_data[i]
        assert type(item) == type(list_data[i])


@pytest.mark.parametrize(
    "dict_data",
    [
        {"str": "value", "int": 42, "float": 3.14, "bool": True, "none": None},
        {"list": [1, 2, 3], "dict": {"nested": "value"}},
        {},
        {
            "datetime": datetime(2023, 1, 1),
            "date": date(2023, 1, 1),
            "decimal": Decimal("10.5"),
        },
        {"complex": {"deeply": {"nested": {"structure": [1, 2, {"final": "level"}]}}}},
    ],
)
@pytest.mark.asyncio
async def test_redis_dict_any_set_functionality_sanity(dict_data):
    # Arrange
    model = AnyModel()
    await model.save()

    # Act
    # Set to empty dict first, then update if there's data
    await model.dict_any.client.json().set(
        model.dict_any.redis_key, model.dict_any.json_path, {}
    )
    if dict_data:
        await model.dict_any.aupdate(**dict_data)

    # Assert
    fresh_model = AnyModel()
    fresh_model.pk = model.pk
    await fresh_model.dict_any.load()
    loaded_value = dict(fresh_model.dict_any)
    assert loaded_value == dict_data
    assert len(loaded_value) == len(dict_data)
    for key, value in loaded_value.items():
        assert value == dict_data[key]
        assert type(value) == type(dict_data[key])


@pytest.mark.asyncio
async def test_redis_any_inheritance_sanity():
    # Arrange & Act
    model = AnyModel(simple_any="test")

    # Assert
    from rapyer.types.any import AnyTypeRedis

    assert isinstance(model.simple_any, AnyTypeRedis)


@pytest.mark.asyncio
async def test_redis_any_clone_functionality_sanity():
    # Arrange
    test_value = {"complex": [1, 2, {"nested": "value"}]}
    model = AnyModel(simple_any=test_value)

    # Act
    cloned_any = model.simple_any.clone()

    # Assert
    assert cloned_any == test_value
    assert type(cloned_any) == type(test_value)


@pytest.mark.asyncio
async def test_redis_any_model_creation_functionality_sanity(real_redis_client):
    # Arrange & Act
    model = AnyModel(simple_any="test")

    # Assert
    from rapyer.types.any import AnyTypeRedis

    assert isinstance(model.simple_any, AnyTypeRedis)
    assert hasattr(model.simple_any, "redis_key")
    assert hasattr(model.simple_any, "field_path")
    assert hasattr(model.simple_any, "client")
    assert hasattr(model.simple_any, "json_path")
    assert model.simple_any.redis_key == model.key
    assert model.simple_any.field_path == "simple_any"
    assert model.simple_any.json_path == "$.simple_any"
    assert model.simple_any.client == real_redis_client


@pytest.mark.asyncio
async def test_redis_any_persistence_across_instances_edge_case():
    # Arrange
    original_value = {"modified": True, "number": 42}
    model1 = AnyModel(simple_any="original")
    await model1.save()
    await model1.simple_any.set(original_value)

    # Act
    model2 = AnyModel()
    model2.pk = model1.pk
    loaded_value = await model2.simple_any.load()

    # Assert
    assert loaded_value == original_value


@pytest.mark.asyncio
async def test_redis_list_any_empty_list_functionality_edge_case():
    # Arrange
    model = AnyModel()
    await model.save()

    # Act
    await model.list_any.client.json().set(
        model.list_any.redis_key, model.list_any.json_path, []
    )

    # Assert
    fresh_model = AnyModel()
    fresh_model.pk = model.pk
    await fresh_model.list_any.load()
    loaded_value = list(fresh_model.list_any)
    assert loaded_value == []
    assert isinstance(loaded_value, list)


@pytest.mark.asyncio
async def test_redis_dict_any_empty_dict_functionality_edge_case():
    # Arrange
    model = AnyModel()
    await model.save()

    # Act
    await model.dict_any.client.json().set(
        model.dict_any.redis_key, model.dict_any.json_path, {}
    )

    # Assert
    fresh_model = AnyModel()
    fresh_model.pk = model.pk
    await fresh_model.dict_any.load()
    loaded_value = dict(fresh_model.dict_any)
    assert loaded_value == {}
    assert isinstance(loaded_value, dict)


@pytest.mark.parametrize(
    "complex_data",
    [
        {
            "mixed_list": [1, "string", {"nested": True}, [1, 2, 3]],
            "nested_dict": {"level1": {"level2": {"level3": "deep"}}},
            "datetime_obj": datetime(2023, 5, 15, 10, 30, 45),
            "none_value": None,
        },
        [
            {"key1": "value1"},
            [1, 2, {"inner": [3, 4]}],
            "string",
            42,
            datetime.now(),
            None,
        ],
    ],
)
@pytest.mark.asyncio
async def test_redis_any_complex_nested_structures_edge_case(complex_data):
    # Arrange
    model = AnyModel()
    await model.save()

    # Act
    await model.simple_any.set(complex_data)

    # Assert
    fresh_model = AnyModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.simple_any.load()
    assert loaded_value == complex_data
    assert type(loaded_value) == type(complex_data)


@pytest.mark.asyncio
async def test_redis_any_serialization_deserialization_consistency_edge_case():
    # Arrange
    test_data = {
        "string": "test",
        "integer": 42,
        "float": 3.14159,
        "boolean": True,
        "none": None,
        "list": [1, 2, 3, "mixed"],
        "dict": {"nested": {"value": True}},
        "datetime": datetime(2023, 1, 1, 12, 0, 0),
        "decimal": Decimal("123.456"),
    }
    model = AnyModel()
    await model.save()

    # Act
    await model.simple_any.set(test_data)
    loaded_value = await model.simple_any.load()

    # Assert
    assert loaded_value == test_data
    for key, value in loaded_value.items():
        assert value == test_data[key]
        assert type(value) == type(test_data[key])


@pytest.mark.asyncio
async def test_redis_any_overwrite_different_types_edge_case():
    # Arrange
    model = AnyModel()
    await model.save()

    # Act & Assert
    # Start with string
    await model.simple_any.set("string_value")
    loaded_value = await model.simple_any.load()
    assert loaded_value == "string_value"
    assert isinstance(loaded_value, str)

    # Overwrite with dict
    dict_value = {"key": "value", "number": 42}
    await model.simple_any.set(dict_value)
    loaded_value = await model.simple_any.load()
    assert loaded_value == dict_value
    assert isinstance(loaded_value, dict)

    # Overwrite with list
    list_value = [1, 2, 3, "mixed"]
    await model.simple_any.set(list_value)
    loaded_value = await model.simple_any.load()
    assert loaded_value == list_value
    assert isinstance(loaded_value, list)
