import pytest
import pytest_asyncio

import redis_pydantic
from redis_pydantic.base import BaseRedisModel
from redis_pydantic.types import ALL_TYPES


class BoolModel(BaseRedisModel):
    is_active: bool = False
    is_deleted: bool = True

    class Meta:
        redis = None
        redis_type = ALL_TYPES


@pytest_asyncio.fixture
async def real_redis_client():
    redis = await redis_pydantic.BaseRedisModel.Meta.redis.from_url(
        "redis://localhost:6371/15"
    )
    BoolModel.Meta.redis = redis
    await redis.flushdb()
    yield redis
    await redis.flushdb()
    await redis.aclose()


@pytest.mark.parametrize("test_values", [True, False])
@pytest.mark.asyncio
async def test_redis_bool_set_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = BoolModel()
    await model.save()

    # Act
    await model.is_active.set(test_values)

    # Assert
    redis_value = (
        await real_redis_client.json().get(model.key, model.is_active.json_path)
    )[0]
    assert redis_value == test_values


@pytest.mark.parametrize("test_values", [True, False])
@pytest.mark.asyncio
async def test_redis_bool_load_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = BoolModel(is_active=test_values)
    await model.save()

    # Act
    loaded_value = await model.is_active.load()

    # Assert
    assert loaded_value == test_values


@pytest.mark.asyncio
async def test_redis_bool_set_with_wrong_type_edge_case(real_redis_client):
    # Arrange
    model = BoolModel()

    # Act & Assert
    with pytest.raises(TypeError, match="Value must be bool"):
        await model.is_active.set("not a bool")


@pytest.mark.asyncio
async def test_redis_bool_inheritance_sanity(real_redis_client):
    # Arrange & Act
    model = BoolModel(is_active=True)

    # Assert
    from redis_pydantic.types.boolean import RedisBool

    assert isinstance(model.is_active, RedisBool)
    assert isinstance(model.is_active, int)  # bool inherits from int in Python
    assert model.is_active == True
    assert model.is_active and True == True
    assert model.is_active or False == True


@pytest.mark.asyncio
async def test_redis_bool_clone_functionality_sanity(real_redis_client):
    # Arrange
    model = BoolModel(is_active=True)

    # Act
    cloned_bool = model.is_active.clone()

    # Assert
    assert isinstance(cloned_bool, bool)
    assert not isinstance(cloned_bool, type(model.is_active))
    assert cloned_bool == True


@pytest.mark.asyncio
async def test_redis_bool_model_creation_functionality_sanity(real_redis_client):
    # Arrange & Act
    model = BoolModel(is_active=True)

    # Assert
    from redis_pydantic.types.boolean import RedisBool

    assert isinstance(model.is_active, RedisBool)
    assert hasattr(model.is_active, "redis_key")
    assert hasattr(model.is_active, "field_path")
    assert hasattr(model.is_active, "redis")
    assert hasattr(model.is_active, "json_path")
    assert model.is_active.redis_key == model.key
    assert model.is_active.field_path == "is_active"
    assert model.is_active.json_path == "$.is_active"
    assert model.is_active.redis == real_redis_client


@pytest.mark.parametrize(
    "operations",
    [
        (lambda x: x and True, True),
        (lambda x: x and False, False),
        (lambda x: x or False, True),
        (lambda x: x or True, True),
        (lambda x: not x, False),
        (lambda x: bool(x), True),
        (lambda x: int(x), 1),
    ],
)
@pytest.mark.asyncio
async def test_redis_bool_logical_operations_sanity(real_redis_client, operations):
    # Arrange
    model = BoolModel(is_active=True)
    operation, expected = operations

    # Act
    result = operation(model.is_active)

    # Assert
    assert result == expected


@pytest.mark.asyncio
async def test_redis_bool_falsy_values_functionality_sanity(real_redis_client):
    # Arrange
    model = BoolModel(is_active=False)

    # Act & Assert
    assert not model.is_active
    assert model.is_active == False
    assert model.is_active == 0  # bool inherits from int


@pytest.mark.asyncio
async def test_redis_bool_truthy_values_functionality_sanity(real_redis_client):
    # Arrange
    model = BoolModel(is_active=True)

    # Act & Assert
    assert model.is_active
    assert model.is_active == True
    assert model.is_active == 1  # bool inherits from int
