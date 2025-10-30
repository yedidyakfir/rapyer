import pytest

from tests.models.simple_types import BoolModel


@pytest.mark.parametrize("test_values", [True, False])
@pytest.mark.asyncio
async def test_redis_bool_set_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = BoolModel()
    await model.save()

    # Act
    model.is_active = test_values
    await model.is_active.save()

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
    with pytest.raises(ValueError, match="Input should be a valid boolean"):
        model.is_active = "not a bool"


@pytest.mark.asyncio
async def test_redis_bool_truthy_values_functionality_sanity():
    # Arrange
    model = BoolModel(is_active=True)

    # Act & Assert
    assert model.is_active
