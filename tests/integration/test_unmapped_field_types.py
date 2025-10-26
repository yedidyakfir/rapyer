from collections import namedtuple
from dataclasses import dataclass
from typing import Union

import pytest
import pytest_asyncio

from rapyer.base import AtomicRedisModel

# from rapyer.types.any import AnyTypeRedis


# Define some unmapped types for testing
CustomType = namedtuple("CustomType", ["value"])


@dataclass
class CustomDataClass:
    value: str


class UnmappedTypesModel(AtomicRedisModel):
    custom_type_field: CustomType = CustomType("default")
    dataclass_field: CustomDataClass = CustomDataClass("default")
    union_field: Union[str, int, CustomType] = "default"


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    UnmappedTypesModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_unmapped_field_types_use_any_redis_type_sanity():
    # Arrange & Act
    model = UnmappedTypesModel()

    # Assert
    assert isinstance(model.custom_type_field, AnyTypeRedis)
    assert isinstance(model.dataclass_field, AnyTypeRedis)
    assert isinstance(model.union_field, AnyTypeRedis)


test_data_args = [
    CustomType("test_value"),
    CustomDataClass("test_data"),
    "string_value",
    42,
]


@pytest.mark.parametrize("test_data", test_data_args)
@pytest.mark.asyncio
async def test_unmapped_field_types_set_and_load_functionality_sanity(test_data):
    # Arrange
    model = UnmappedTypesModel()
    await model.save()

    # Act
    await model.custom_type_field.set(test_data)

    # Assert
    fresh_model = UnmappedTypesModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.custom_type_field.load()
    assert loaded_value == test_data
    assert type(loaded_value) == type(test_data)


@pytest.mark.asyncio
async def test_unmapped_field_types_persistence_edge_case():
    # Arrange
    custom_data = CustomType("persistent_value")
    model = UnmappedTypesModel()
    await model.save()
    await model.custom_type_field.set(custom_data)

    # Act
    fresh_model = UnmappedTypesModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.custom_type_field.load()

    # Assert
    assert loaded_value == custom_data
    assert isinstance(loaded_value, CustomType)
    assert loaded_value.value == "persistent_value"


@pytest.mark.asyncio
async def test_unmapped_dataclass_field_functionality_sanity():
    # Arrange
    dataclass_data = CustomDataClass("dataclass_test")
    model = UnmappedTypesModel()
    await model.save()

    # Act
    await model.dataclass_field.set(dataclass_data)

    # Assert
    fresh_model = UnmappedTypesModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.dataclass_field.load()
    assert loaded_value == dataclass_data
    assert isinstance(loaded_value, CustomDataClass)
    assert loaded_value.value == "dataclass_test"
