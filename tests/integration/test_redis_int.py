import pytest
import pytest_asyncio

from rapyer.base import AtomicRedisModel


class IntModel(AtomicRedisModel):
    count: int = 0
    score: int = 100


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    IntModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize("test_values", [42, -100, 0, 999, -999])
@pytest.mark.asyncio
async def test_redis_int_set_functionality_sanity(test_values):
    # Arrange
    model = IntModel()
    await model.save()

    # Act
    await model.count.set(test_values)

    # Assert
    fresh_model = IntModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.count.load()
    assert loaded_value == test_values


@pytest.mark.parametrize("test_values", [42, -100, 0, 999, -999])
@pytest.mark.asyncio
async def test_redis_int_load_functionality_sanity(test_values):
    # Arrange
    model = IntModel()
    await model.save()
    await model.count.set(test_values)

    # Act
    fresh_model = IntModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.count.load()

    # Assert
    assert loaded_value == test_values


@pytest.mark.asyncio
async def test_redis_int_load_with_none_value_edge_case():
    # Arrange
    model = IntModel()

    # Act
    loaded_value = await model.count.load()

    # Assert
    assert loaded_value is None


@pytest.mark.parametrize("redis_values", [4_2, 43])
@pytest.mark.asyncio
async def test_redis_int_load_type_conversion_edge_case(
    real_redis_client, redis_values
):
    # Arrange
    model = IntModel()
    await model.save()
    await real_redis_client.json().set(model.key, model.count.json_path, redis_values)

    # Act
    fresh_model = IntModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.count.load()

    # Assert
    assert loaded_value == int(redis_values)


@pytest.mark.asyncio
async def test_redis_int_set_with_wrong_type_edge_case():
    # Arrange
    model = IntModel()

    # Act & Assert
    with pytest.raises(TypeError, match="Value must be int"):
        await model.count.set("not an int")


@pytest.mark.asyncio
async def test_redis_int_inheritance_sanity():
    # Arrange & Act
    model = IntModel(count=42)

    # Assert
    from rapyer.types.integer import RedisInt

    assert isinstance(model.count, RedisInt)
    assert isinstance(model.count, int)
    assert model.count == 42
    assert model.count + 10 == 52
    assert model.count - 5 == 37


@pytest.mark.asyncio
async def test_redis_int_clone_functionality_sanity():
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
    from rapyer.types.integer import RedisInt

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
async def test_redis_int_persistence_across_instances_edge_case():
    # Arrange
    model1 = IntModel(count=100)
    await model1.save()
    await model1.count.set(100)

    # Act
    model2 = IntModel()
    model2.pk = model1.pk
    loaded_value = await model2.count.load()

    # Assert
    assert loaded_value == 100


@pytest.mark.parametrize(
    "operations",
    [
        (lambda x: x + 10, 52),
        (lambda x: x - 8, 34),
        (lambda x: x * 2, 84),
        (lambda x: x == 42, True),
        (lambda x: x > 40, True),
        (lambda x: x < 40, False),
    ],
)
@pytest.mark.asyncio
async def test_redis_int_arithmetic_operations_sanity(operations):
    # Arrange
    model = IntModel(count=42)
    operation, expected = operations

    # Act
    result = operation(model.count)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "initial_value,increase_amount,expected",
    [
        (0, 1, 1),
        (10, 5, 15),
        (100, -20, 80),
        (-50, 30, -20),
        (0, 0, 0),
        (999, 1, 1000),
        (-999, -1, -1000),
    ],
)
@pytest.mark.asyncio
async def test_redis_int_increase_functionality_sanity(
    initial_value, increase_amount, expected
):
    # Arrange
    model = IntModel()
    await model.save()
    await model.count.set(initial_value)

    # Act
    result = await model.count.increase(increase_amount)

    # Assert
    fresh_model = IntModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.count.load()
    assert loaded_value == expected
    assert result == expected


@pytest.mark.asyncio
async def test_redis_int_increase_default_amount_sanity():
    # Arrange
    model = IntModel()
    await model.save()
    await model.count.set(10)

    # Act
    result = await model.count.increase()

    # Assert
    fresh_model = IntModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.count.load()
    assert loaded_value == 11
    assert result == 11


@pytest.mark.asyncio
async def test_redis_int_increase_on_non_existent_key_edge_case():
    # Arrange
    model = IntModel()
    await model.save()

    # Act
    result = await model.count.increase(5)

    # Assert
    fresh_model = IntModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.count.load()
    assert loaded_value == 5
    assert result == 5


@pytest.mark.asyncio
async def test_redis_int_increase_multiple_times_sanity():
    # Arrange
    model = IntModel(count=0)
    await model.save()

    # Act
    result1 = await model.count.increase(10)
    result2 = await model.count.increase(20)
    result3 = await model.count.increase(-5)

    # Assert
    fresh_model = IntModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.count.load()
    assert result1 == 10
    assert result2 == 30
    assert result3 == 25
    assert loaded_value == 25
