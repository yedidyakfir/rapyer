from typing import List, Dict, Optional

import pytest
import pytest_asyncio

from redis_pydantic.base import BaseRedisModel


class NoneTestModel(BaseRedisModel):
    optional_string: Optional[str] = None
    optional_int: Optional[int] = None
    optional_bool: Optional[bool] = None
    optional_bytes: Optional[bytes] = None
    optional_list: Optional[List[str]] = None
    optional_dict: Optional[Dict[str, str]] = None


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    NoneTestModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize(
    "field_name",
    [
        "optional_string",
        "optional_int",
        "optional_bool",
        "optional_bytes",
        "optional_list",
        "optional_dict",
    ],
)
@pytest.mark.asyncio
async def test_none_values_persistence_sanity(real_redis_client, field_name):
    # Arrange
    model = NoneTestModel()
    assert getattr(model, field_name) is None

    # Act
    await model.save()
    retrieved_model = await NoneTestModel.get(model.key)

    # Assert
    assert getattr(retrieved_model, field_name) is None


@pytest.mark.asyncio
async def test_all_none_values_model_persistence_sanity(real_redis_client):
    # Arrange
    model = NoneTestModel()

    # Act
    await model.save()
    retrieved_model = await NoneTestModel.get(model.key)

    # Assert
    assert retrieved_model.optional_string is None
    assert retrieved_model.optional_int is None
    assert retrieved_model.optional_bool is None
    assert retrieved_model.optional_bytes is None
    assert retrieved_model.optional_list is None
    assert retrieved_model.optional_dict is None


@pytest.mark.asyncio
async def test_mixed_none_and_values_persistence_edge_case(real_redis_client):
    # Arrange
    model = NoneTestModel(
        optional_string="test",
        optional_int=None,
        optional_bool=True,
        optional_bytes=None,
        optional_list=["item1"],
        optional_dict=None,
    )

    # Act
    await model.save()
    retrieved_model = await NoneTestModel.get(model.key)

    # Assert
    assert retrieved_model.optional_string == "test"
    assert retrieved_model.optional_int is None
    assert retrieved_model.optional_bool == True
    assert retrieved_model.optional_bytes is None
    assert retrieved_model.optional_list == ["item1"]
    assert retrieved_model.optional_dict is None


@pytest.mark.asyncio
async def test_set_value_to_none_after_initialization_edge_case(real_redis_client):
    # Arrange
    model = NoneTestModel(
        optional_string="initial_value",
        optional_int=42,
        optional_list=["item1", "item2"],
    )

    # Act
    model.optional_string = None
    model.optional_int = None
    model.optional_list = None
    await model.save()
    retrieved_model = await NoneTestModel.get(model.key)

    # Assert
    assert retrieved_model.optional_string is None
    assert retrieved_model.optional_int is None
    assert retrieved_model.optional_list is None
