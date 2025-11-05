from datetime import datetime

import pytest
from pydantic import Field, BaseModel

from rapyer.base import AtomicRedisModel
from rapyer.types.dct import RedisDict
from rapyer.types.lst import RedisList
from rapyer.types.string import RedisStr
from rapyer.types.integer import RedisInt
from rapyer.types.byte import RedisBytes
from rapyer.types.datetime import RedisDatetime
from rapyer.types.base import RedisType
from tests.models.collection_types import (
    IntDictModel,
    StrDictModel,
    BytesDictModel,
    DatetimeDictModel,
    EnumDictModel,
    AnyDictModel,
    Status,
    BaseDictMetadataModel,
)


# Test models with default values for supported Redis types
class DefaultStrModel(AtomicRedisModel):
    name: str = "default_name"
    description: str = ""


class DefaultIntModel(AtomicRedisModel):
    count: int = 42
    score: int = 0


class DefaultBoolModel(AtomicRedisModel):
    is_active: bool = True
    is_deleted: bool = False


class DefaultBytesModel(AtomicRedisModel):
    data: bytes = b"default_data"
    binary: bytes = b""


class DefaultDatetimeModel(AtomicRedisModel):
    created_at: datetime = Field(default_factory=datetime.now)


class DefaultListModel(AtomicRedisModel):
    tags: list[str] = Field(default_factory=list)
    numbers: list[int] = Field(default_factory=lambda: [1, 2, 3])


class DefaultDictModel(AtomicRedisModel):
    metadata: dict[str, str] = Field(default_factory=dict)
    settings: dict[str, int] = Field(default_factory=lambda: {"key": 100})

class InnerModel(BaseModel):
    value: str = "inner_default"
    counter: int = 0


class DefaultNestedModel(AtomicRedisModel):
    inner: InnerModel = Field(default_factory=InnerModel)
    name: str = "outer_default"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "field_name", "expected_redis_type", "expected_json_path"],
    [
        [DefaultStrModel, "name", RedisStr, "$.name"],
        [DefaultStrModel, "description", RedisStr, "$.description"],
        [DefaultIntModel, "count", RedisInt, "$.count"],
        [DefaultIntModel, "score", RedisInt, "$.score"],
        [DefaultBytesModel, "data", RedisBytes, "$.data"],
        [DefaultBytesModel, "binary", RedisBytes, "$.binary"],
        [DefaultListModel, "tags", RedisList, "$.tags"],
        [DefaultListModel, "numbers", RedisList, "$.numbers"],
        [DefaultDictModel, "metadata", RedisDict, "$.metadata"],
        [DefaultDictModel, "settings", RedisDict, "$.settings"],
    ],
)
async def test_model_creation_with_defaults__check_redis_type_inheritance_and_json_path_sanity(
    model_class: type[AtomicRedisModel],
    field_name: str,
    expected_redis_type: type,
    expected_json_path: str,
):
    # Arrange & Act
    model = model_class()

    # Assert
    field_value = getattr(model, field_name)
    assert isinstance(field_value, expected_redis_type)
    assert isinstance(field_value, RedisType) or isinstance(
        field_value, AtomicRedisModel
    )
    assert field_value.json_path == expected_json_path


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "field_name", "expected_default_value"],
    [
        [DefaultStrModel, "name", "default_name"],
        [DefaultStrModel, "description", ""],
        [DefaultIntModel, "count", 42],
        [DefaultIntModel, "score", 0],
        [DefaultBoolModel, "is_active", True],
        [DefaultBoolModel, "is_deleted", False],
        [DefaultBytesModel, "data", b"default_data"],
        [DefaultBytesModel, "binary", b""],
        [DefaultListModel, "tags", []],
        [DefaultListModel, "numbers", [1, 2, 3]],
        [DefaultDictModel, "metadata", {}],
        [DefaultDictModel, "settings", {"key": 100}],
    ],
)
async def test_model_creation_with_defaults__check_default_values_sanity(
    model_class: type[AtomicRedisModel], field_name: str, expected_default_value
):
    # Arrange & Act
    model = model_class()

    # Assert
    field_value = getattr(model, field_name)
    assert field_value == expected_default_value


@pytest.mark.asyncio
async def test_model_creation_with_nested_base_model__check_atomic_base_inheritance_and_json_path_sanity():
    # Arrange & Act
    model = DefaultNestedModel()

    # Assert
    assert isinstance(model.inner, AtomicRedisModel)
    assert model.inner.json_path == "$.inner"
    assert model.inner.value == "inner_default"
    assert model.inner.counter == 0


@pytest.mark.asyncio
async def test_model_creation_with_datetime_field__check_datetime_default_factory_sanity():
    # Arrange & Act
    model = DefaultDatetimeModel()

    # Assert
    assert isinstance(model.created_at, RedisDatetime)
    assert isinstance(model.created_at, datetime)
    assert model.created_at.json_path == "$.created_at"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data"],
    [
        [StrDictModel, {"key1": "value1"}],
        [IntDictModel, {"key1": 42}],
        [DatetimeDictModel, {"key1": datetime(2023, 1, 1)}],
        [BytesDictModel, {"key1": b"data1"}],
        [EnumDictModel, {"key1": Status.ACTIVE}],
        [AnyDictModel, {"key1": "mixed"}],
    ],
)
async def test_redis_dict__model_creation__check_redis_dict_instance_sanity(
    model_class: type[BaseDictMetadataModel], initial_data
):
    # Arrange & Act
    user = model_class(metadata=initial_data)

    # Assert
    assert isinstance(user.metadata, RedisDict)
    assert hasattr(user.metadata, "key")
    assert hasattr(user.metadata, "field_path")
    assert hasattr(user.metadata, "redis")
    assert hasattr(user.metadata, "json_path")
    assert user.metadata.key == user.key
    assert user.metadata.field_path == ".metadata"
    assert user.metadata.json_path == "$.metadata"
