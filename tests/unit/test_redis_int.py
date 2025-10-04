import pytest
import pytest_asyncio

import redis_pydantic
from redis_pydantic.base import BaseRedisModel
from redis_pydantic.types import ALL_TYPES


class IntModel(BaseRedisModel):
    count: int = 0
    score: int = 100

    class Meta:
        redis = None
        redis_type = ALL_TYPES


@pytest_asyncio.fixture
async def real_redis_client():
    redis = await redis_pydantic.BaseRedisModel.Meta.redis.from_url(
        "redis://localhost:6371/0"
    )
    IntModel.Meta.redis = redis
    await redis.flushall()
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest.mark.parametrize("test_values", [42, -100, 0, 999, -999])
@pytest.mark.asyncio
async def test_redis_int_set_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = IntModel()

    # Act
    await model.count.set(test_values)

    # Assert
    redis_value = await real_redis_client.json().get(model.key, model.count.json_path)
    assert redis_value == test_values


@pytest.mark.parametrize("test_values", [42, -100, 0, 999, -999])
@pytest.mark.asyncio
async def test_redis_int_load_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = IntModel()
    await real_redis_client.json().set(model.key, model.count.json_path, test_values)

    # Act
    loaded_value = await model.count.load()

    # Assert
    assert loaded_value == test_values


@pytest.mark.asyncio
async def test_redis_int_load_with_none_value_edge_case(real_redis_client):
    # Arrange
    model = IntModel()

    # Act
    loaded_value = await model.count.load()

    # Assert
    assert loaded_value == 0


@pytest.mark.parametrize("redis_values", ["42", 42.5, "invalid"])
@pytest.mark.asyncio
async def test_redis_int_load_type_conversion_edge_case(real_redis_client, redis_values):
    # Arrange
    model = IntModel()
    await real_redis_client.json().set(model.key, model.count.json_path, redis_values)

    # Act
    loaded_value = await model.count.load()

    # Assert
    if redis_values == "42":
        assert loaded_value == 42
    elif redis_values == 42.5:
        assert loaded_value == 42
    elif redis_values == "invalid":
        assert loaded_value == 0


@pytest.mark.asyncio
async def test_redis_int_set_with_wrong_type_edge_case(real_redis_client):
    # Arrange
    model = IntModel()

    # Act & Assert
    with pytest.raises(TypeError, match="Value must be int"):
        await model.count.set("not an int")


@pytest.mark.asyncio
async def test_redis_int_inheritance_sanity(real_redis_client):
    # Arrange & Act
    model = IntModel(count=42)

    # Assert
    from redis_pydantic.types.integer import RedisInt
    assert isinstance(model.count, RedisInt)
    assert isinstance(model.count, int)
    assert model.count == 42
    assert model.count + 10 == 52
    assert model.count - 5 == 37


@pytest.mark.asyncio
async def test_redis_int_clone_functionality_sanity(real_redis_client):
    # Arrange
    model = IntModel(count=42)

    # Act
    cloned_int = model.count.clone()

    # Assert
    assert isinstance(cloned_int, int)
    assert not isinstance(cloned_int, type(model.count))
    assert cloned_int == 42


@pytest.mark.asyncio
async def test_redis_int_model_creation_functionality_sanity(real_redis_client):
    # Arrange & Act
    model = IntModel(count=42)

    # Assert
    from redis_pydantic.types.integer import RedisInt
    assert isinstance(model.count, RedisInt)
    assert hasattr(model.count, "redis_key")
    assert hasattr(model.count, "field_path")
    assert hasattr(model.count, "redis")
    assert hasattr(model.count, "json_path")
    assert model.count.redis_key == model.key
    assert model.count.field_path == "count"
    assert model.count.json_path == "$.count"
    assert model.count.redis == real_redis_client


@pytest.mark.asyncio
async def test_redis_int_persistence_across_instances_edge_case(real_redis_client):
    # Arrange
    model1 = IntModel(count=100)
    await model1.count.set(100)

    # Act
    model2 = IntModel()
    model2.pk = model1.pk
    loaded_value = await model2.count.load()

    # Assert
    assert loaded_value == 100


@pytest.mark.parametrize("operations", [
    (lambda x: x + 10, 52),
    (lambda x: x - 8, 34),
    (lambda x: x * 2, 84),
    (lambda x: x == 42, True),
    (lambda x: x > 40, True),
    (lambda x: x < 40, False)
])
@pytest.mark.asyncio
async def test_redis_int_arithmetic_operations_sanity(real_redis_client, operations):
    # Arrange
    model = IntModel(count=42)
    operation, expected = operations

    # Act
    result = operation(model.count)

    # Assert
    assert result == expected