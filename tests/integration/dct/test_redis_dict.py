from datetime import datetime
from enum import Enum
from typing import Any

import pytest
import pytest_asyncio
from pydantic import BaseModel, Field

from rapyer.base import AtomicRedisModel
from rapyer.types.dct import RedisDict


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class StrDictModel(AtomicRedisModel):
    metadata: dict[str, str] = Field(default_factory=dict)


class IntDictModel(AtomicRedisModel):
    metadata: dict[str, int] = Field(default_factory=dict)


class BytesDictModel(AtomicRedisModel):
    metadata: dict[str, bytes] = Field(default_factory=dict)


class DatetimeDictModel(AtomicRedisModel):
    metadata: dict[str, datetime] = Field(default_factory=dict)


class EnumDictModel(AtomicRedisModel):
    metadata: dict[str, Status] = Field(default_factory=dict)


class AnyDictModel(AtomicRedisModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


# Additional complex types
class Person(BaseModel):
    name: str
    age: int
    email: str


class Company(BaseModel):
    name: str
    employees: int
    founded: int


class BaseModelDictModel(AtomicRedisModel):
    metadata: dict[str, Person] = Field(default_factory=dict)


class BoolDictModel(AtomicRedisModel):
    metadata: dict[str, bool] = Field(default_factory=dict)


class ListDictModel(AtomicRedisModel):
    metadata: dict[str, list[str]] = Field(default_factory=dict)


class NestedDictModel(AtomicRedisModel):
    metadata: dict[str, dict[str, str]] = Field(default_factory=dict)


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    StrDictModel.Meta.redis = redis_client
    IntDictModel.Meta.redis = redis_client
    BytesDictModel.Meta.redis = redis_client
    DatetimeDictModel.Meta.redis = redis_client
    EnumDictModel.Meta.redis = redis_client
    AnyDictModel.Meta.redis = redis_client
    BaseModelDictModel.Meta.redis = redis_client
    BoolDictModel.Meta.redis = redis_client
    ListDictModel.Meta.redis = redis_client
    NestedDictModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data", "new_item_key", "new_item_value"],
    [
        [StrDictModel, {"key1": "value1"}, "key2", "value2"],
        [IntDictModel, {"key1": 42}, "key2", 100],
        [BytesDictModel, {"key1": b"data1"}, "key2", b"data2"],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1)},
            "key2",
            datetime(2023, 2, 1),
        ],
        [EnumDictModel, {"key1": Status.ACTIVE}, "key2", Status.PENDING],
        [AnyDictModel, {"key1": "mixed"}, "key2", 42],
        [
            BaseModelDictModel,
            {"key1": Person(name="Alice", age=30, email="alice@example.com")},
            "key2",
            Person(name="Bob", age=25, email="bob@example.com"),
        ],
        [BoolDictModel, {"key1": True}, "key2", False],
        [ListDictModel, {"key1": ["item1", "item2"]}, "key2", ["item3", "item4"]],
        [
            NestedDictModel,
            {"key1": {"nested1": "value1"}},
            "key2",
            {"nested2": "value2"},
        ],
    ],
)
async def test_redis_dict__setitem__check_local_consistency_sanity(
    model_class: type[AtomicRedisModel], initial_data, new_item_key, new_item_value
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()

    # Act
    await user.metadata.aset_item(new_item_key, new_item_value)
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = model_class()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data", "key_to_delete"],
    [
        [StrDictModel, {"key1": "value1", "key2": "value2"}, "key1"],
        [IntDictModel, {"key1": 42, "key2": 100}, "key1"],
        [BytesDictModel, {"key1": b"data1", "key2": b"data2"}, "key1"],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1), "key2": datetime(2023, 2, 1)},
            "key1",
        ],
        [EnumDictModel, {"key1": Status.ACTIVE, "key2": Status.PENDING}, "key1"],
        [AnyDictModel, {"key1": "mixed", "key2": 42}, "key1"],
    ],
)
async def test_redis_dict__delitem__check_local_consistency_sanity(
    model_class, initial_data, key_to_delete
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()

    # Act
    await user.metadata.adel_item(key_to_delete)
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = model_class()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data", "update_data"],
    [
        [StrDictModel, {"key1": "value1"}, {"key2": "value2", "key3": "value3"}],
        [IntDictModel, {"key1": 42}, {"key2": 100, "key3": 200}],
        [BytesDictModel, {"key1": b"data1"}, {"key2": b"data2", "key3": b"data3"}],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1)},
            {"key2": datetime(2023, 2, 1), "key3": datetime(2023, 3, 1)},
        ],
        [
            EnumDictModel,
            {"key1": Status.ACTIVE},
            {"key2": Status.PENDING, "key3": Status.INACTIVE},
        ],
        [AnyDictModel, {"key1": "mixed"}, {"key2": 42, "key3": [1, 2, 3]}],
    ],
)
async def test_redis_dict__update__check_local_consistency_sanity(
    model_class: type[AtomicRedisModel], initial_data, update_data
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()

    # Act
    await user.metadata.aupdate(**update_data)
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = model_class()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data"],
    [
        [StrDictModel, {"key1": "value1", "key2": "value2"}],
        [IntDictModel, {"key1": 42, "key2": 100}],
        [BytesDictModel, {"key1": b"data1", "key2": b"data2"}],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1), "key2": datetime(2023, 2, 1)},
        ],
        [EnumDictModel, {"key1": Status.ACTIVE, "key2": Status.PENDING}],
        [AnyDictModel, {"key1": "mixed", "key2": 42}],
    ],
)
async def test_redis_dict__clear__check_local_consistency_sanity(
    model_class, initial_data
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()

    # Act
    await user.metadata.aclear()
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = model_class()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert len(user.metadata) == 0
    assert user.metadata == fresh_user.metadata


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data", "new_item_key", "new_item_value"],
    [
        [StrDictModel, {"key1": "value1"}, "key2", "value2"],
        [IntDictModel, {"key1": 42}, "key2", 100],
        [BytesDictModel, {"key1": b"data1"}, "key2", b"data2"],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1)},
            "key2",
            datetime(2023, 2, 1),
        ],
        [EnumDictModel, {"key1": Status.ACTIVE}, "key2", Status.PENDING],
        [AnyDictModel, {"key1": "mixed"}, "key2", 42],
    ],
)
async def test_redis_dict__load__check_redis_load_sanity(
    model_class, initial_data, new_item_key, new_item_value
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()
    # Use another user instance to set a value and verify load works
    other_user = model_class()
    other_user.pk = user.pk
    await other_user.metadata.load()
    await other_user.metadata.aset_item(new_item_key, new_item_value)

    # Act
    await user.metadata.load()

    # Assert
    fresh_user = model_class()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
    assert new_item_key in user.metadata
    assert user.metadata[new_item_key] == new_item_value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data", "key_to_pop", "expected_value"],
    [
        [StrDictModel, {"key1": "value1", "key2": "value2"}, "key1", "value1"],
        [IntDictModel, {"key1": 42, "key2": 100}, "key1", 42],
        [BytesDictModel, {"key1": b"data1", "key2": b"data2"}, "key1", b"data1"],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1), "key2": datetime(2023, 2, 1)},
            "key1",
            datetime(2023, 1, 1),
        ],
        [
            EnumDictModel,
            {"key1": Status.ACTIVE, "key2": Status.PENDING},
            "key1",
            Status.ACTIVE,
        ],
        [AnyDictModel, {"key1": "mixed", "key2": 42}, "key1", "mixed"],
    ],
)
async def test_redis_dict__pop__check_redis_pop_sanity(
    model_class, initial_data, key_to_pop, expected_value
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()

    # Act
    popped_value = await user.metadata.apop(key_to_pop)

    # Assert
    fresh_user = model_class()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
    assert popped_value == expected_value
    assert key_to_pop not in user.metadata
    assert len(user.metadata) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data", "default_value"],
    [
        [StrDictModel, {"key1": "value1"}, "default_value"],
        [IntDictModel, {"key1": 42}, 999],
        [BytesDictModel, {"key1": b"data1"}, b"default"],
        [DatetimeDictModel, {"key1": datetime(2023, 1, 1)}, datetime(2023, 12, 31)],
        [EnumDictModel, {"key1": Status.ACTIVE}, Status.INACTIVE],
        [AnyDictModel, {"key1": "mixed"}, "default_any"],
    ],
)
async def test_redis_dict__pop_with_default__check_default_return_sanity(
    model_class, initial_data, default_value
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()

    # Act
    result = await user.metadata.apop("nonexistent", default_value)

    # Assert
    assert result == default_value
    assert len(user.metadata) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data"],
    [
        [StrDictModel, {"key1": "value1", "key2": "value2"}],
        [IntDictModel, {"key1": 42, "key2": 100}],
        [BytesDictModel, {"key1": b"data1", "key2": b"data2"}],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1), "key2": datetime(2023, 2, 1)},
        ],
        [EnumDictModel, {"key1": Status.ACTIVE, "key2": Status.PENDING}],
        [AnyDictModel, {"key1": "mixed", "key2": 42}],
    ],
)
async def test_redis_dict__popitem__check_redis_popitem_sanity(
    model_class, initial_data
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()

    # Act
    popped_value = await user.metadata.apopitem()

    # Assert
    fresh_user = model_class()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
    # popitem should remove one item, leaving one remaining
    assert len(user.metadata) == 1
    # Verify that one of the original values was removed by checking remaining values
    remaining_values = set(user.metadata.values())
    original_values = set(initial_data.values())
    removed_values = original_values - remaining_values
    assert len(removed_values) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data", "update_data"],
    [
        [StrDictModel, {"key1": "value1"}, {"key2": "value2", "key3": "value3"}],
        [IntDictModel, {"key1": 42}, {"key2": 100, "key3": 200}],
        [BytesDictModel, {"key1": b"data1"}, {"key2": b"data2", "key3": b"data3"}],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1)},
            {"key2": datetime(2023, 2, 1), "key3": datetime(2023, 3, 1)},
        ],
        [
            EnumDictModel,
            {"key1": Status.ACTIVE},
            {"key2": Status.PENDING, "key3": Status.INACTIVE},
        ],
        [AnyDictModel, {"key1": "mixed"}, {"key2": 42, "key3": [1, 2, 3]}],
    ],
)
async def test_redis_dict__update_with_dict_arg__check_local_consistency_sanity(
    model_class, initial_data, update_data
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()

    # Act
    await user.metadata.aupdate(**update_data)
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = model_class()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
    assert len(user.metadata) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data"],
    [
        [StrDictModel, {"key1": "value1"}],
        [IntDictModel, {"key1": 42}],
        [BytesDictModel, {"key1": b"data1"}],
        [DatetimeDictModel, {"key1": datetime(2023, 1, 1)}],
        [EnumDictModel, {"key1": Status.ACTIVE}],
        [AnyDictModel, {"key1": "mixed"}],
    ],
)
async def test_redis_dict__update_with_kwargs__check_local_consistency_sanity(
    model_class, initial_data
):
    # Arrange
    user = model_class(metadata=initial_data)
    await user.save()

    # Act
    if model_class == StrDictModel:
        await user.metadata.aupdate(key2="value2", key3="value3")
    elif model_class == IntDictModel:
        await user.metadata.aupdate(key2=100, key3=200)
    elif model_class == BytesDictModel:
        await user.metadata.aupdate(key2=b"data2", key3=b"data3")
    elif model_class == DatetimeDictModel:
        await user.metadata.aupdate(
            key2=datetime(2023, 2, 1), key3=datetime(2023, 3, 1)
        )
    elif model_class == EnumDictModel:
        await user.metadata.aupdate(key2=Status.PENDING, key3=Status.INACTIVE)
    elif model_class == AnyDictModel:
        await user.metadata.aupdate(key2=42, key3=[1, 2, 3])
    await user.save()  # Sync with Redis

    # Assert
    fresh_user = model_class()
    fresh_user.pk = user.pk
    await fresh_user.metadata.load()
    assert user.metadata == fresh_user.metadata
    assert len(user.metadata) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data"],
    [
        [StrDictModel, {"key1": "value1", "key2": "value2"}],
        [IntDictModel, {"key1": 42, "key2": 100}],
        [BytesDictModel, {"key1": b"data1", "key2": b"data2"}],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1), "key2": datetime(2023, 2, 1)},
        ],
        [EnumDictModel, {"key1": Status.ACTIVE, "key2": Status.PENDING}],
        [AnyDictModel, {"key1": "mixed", "key2": 42}],
    ],
)
async def test_redis_dict__clone__check_clone_functionality_sanity(
    model_class, initial_data
):
    # Arrange
    user = model_class(metadata=initial_data)

    # Act
    cloned_dict = user.metadata.clone()

    # Assert
    assert isinstance(cloned_dict, dict)
    assert not isinstance(
        cloned_dict, type(user.metadata)
    )  # Should be regular dict, not RedisDict
    assert cloned_dict == initial_data
    assert cloned_dict == user.metadata
    # Verify it's a copy, not the same object
    if model_class == StrDictModel:
        cloned_dict["key3"] = "value3"
    elif model_class == IntDictModel:
        cloned_dict["key3"] = 200
    elif model_class == BytesDictModel:
        cloned_dict["key3"] = b"data3"
    elif model_class == DatetimeDictModel:
        cloned_dict["key3"] = datetime(2023, 3, 1)
    elif model_class == EnumDictModel:
        cloned_dict["key3"] = Status.INACTIVE
    elif model_class == AnyDictModel:
        cloned_dict["key3"] = [1, 2, 3]
    assert "key3" not in user.metadata


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model_class",
    [
        StrDictModel,
        IntDictModel,
        BytesDictModel,
        DatetimeDictModel,
        EnumDictModel,
        AnyDictModel,
    ],
)
async def test_redis_dict__popitem_empty_dict__check_key_error_sanity(model_class):
    # Arrange
    user = model_class(metadata={})
    await user.save()

    # Act & Assert
    with pytest.raises(KeyError, match="popitem\\(\\): dictionary is empty"):
        await user.metadata.apopitem()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data"],
    [
        [StrDictModel, {"key1": "value1"}],
        [IntDictModel, {"key1": 42}],
        [BytesDictModel, {"key1": b"data1"}],
        [DatetimeDictModel, {"key1": datetime(2023, 1, 1)}],
        [EnumDictModel, {"key1": Status.ACTIVE}],
        [AnyDictModel, {"key1": "mixed"}],
    ],
)
async def test_redis_dict__model_creation__check_redis_dict_instance_sanity(
    real_redis_client, model_class, initial_data
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
    assert user.metadata.field_path == "metadata"
    assert user.metadata.json_path == "$.metadata"
    assert user.metadata.redis == real_redis_client


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data", "additional_data"],
    [
        [StrDictModel, {"key1": "value1"}, {"key2": "value2"}],
        [IntDictModel, {"key1": 42}, {"key2": 100}],
        [BytesDictModel, {"key1": b"data1"}, {"key2": b"data2"}],
        [
            DatetimeDictModel,
            {"key1": datetime(2023, 1, 1)},
            {"key2": datetime(2023, 2, 1)},
        ],
        [EnumDictModel, {"key1": Status.ACTIVE}, {"key2": Status.PENDING}],
        [AnyDictModel, {"key1": "mixed"}, {"key2": 42}],
    ],
)
async def test__redis_dict_model__ior_sanity(
    model_class, initial_data, additional_data
):
    # Arrange
    user = model_class(metadata=initial_data)

    # Act
    user.metadata |= additional_data

    # Assert
    expected_result = {**initial_data, **additional_data}
    assert user.metadata == expected_result
    assert isinstance(user.metadata, RedisDict)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "default_value"],
    [
        [StrDictModel, "default_value"],
        [IntDictModel, 999],
        [BytesDictModel, b"default"],
        [DatetimeDictModel, datetime(2023, 12, 31)],
        [EnumDictModel, Status.INACTIVE],
        [AnyDictModel, "default_any"],
    ],
)
async def test_redis_dict__apop_empty_redis__check_default_returned_sanity(
    model_class, default_value
):
    # Arrange
    user = model_class()
    await user.save()

    # Act
    result = await user.metadata.apop("nonexistent_key", default_value)

    # Assert
    assert result == default_value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "model_class",
    [
        StrDictModel,
        IntDictModel,
        BytesDictModel,
        DatetimeDictModel,
        EnumDictModel,
        AnyDictModel,
    ],
)
async def test_redis_dict__apop_empty_redis__check_no_default_sanity(model_class):
    # Arrange
    user = model_class()
    await user.save()

    # Act
    result = await user.metadata.apop("nonexistent_key", default=None)

    # Assert
    assert result is None
