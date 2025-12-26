import pytest

from tests.models.simple_types import FloatModel


@pytest.mark.parametrize("test_values", [42.5, -100.75, 0.0, 999.99, -999.1, 3.14159])
@pytest.mark.asyncio
async def test_redis_float_load_functionality_sanity(test_values):
    # Arrange
    model = FloatModel()
    await model.asave()
    model.value = test_values
    await model.value.asave()

    # Act
    fresh_model = FloatModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.value.aload()

    # Assert
    assert loaded_value == test_values


@pytest.mark.parametrize(
    ["initial_value", "increase_amount", "expected"],
    [
        [0.0, 1.5, 1.5],
        [10.5, 5.25, 15.75],
    ],
)
@pytest.mark.asyncio
async def test_redis_float_increase_functionality_sanity(
    initial_value, increase_amount, expected
):
    # Arrange
    model = FloatModel()
    await model.asave()
    model.value = initial_value
    await model.value.asave()

    # Act
    result = await model.value.aincrease(increase_amount)

    # Assert
    fresh_model = FloatModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.value.aload()
    assert loaded_value == expected
    assert result == expected
