import pytest
import pytest_asyncio

from rapyer.base import AtomicRedisModel


class BoolModel(AtomicRedisModel):
    is_active: bool = False
    is_deleted: bool = True


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    BoolModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


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
async def test_redis_bool_load_functionality_sanity(test_values):
    # Arrange
    model = BoolModel(is_active=test_values)
    await model.save()

    # Act
    loaded_value = await model.is_active.load()

    # Assert
    assert loaded_value == test_values


@pytest.mark.asyncio
async def test_redis_bool_set_with_wrong_type_edge_case():
    # Arrange
    model = BoolModel()
    await model.save()

    # Act & Assert
    with pytest.raises(TypeError, match="Value must be bool"):
        await model.is_active.set("not a bool")


@pytest.mark.asyncio
async def test_redis_bool_truthy_values_functionality_sanity():
    # Arrange
    model = BoolModel(is_active=True)

    # Act & Assert
    assert model.is_active
