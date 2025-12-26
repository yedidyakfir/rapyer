import pytest

from rapyer.types.float import RedisFloat
from tests.models.simple_types import FloatModel
from tests.models.unit_types import SimpleFloatModel


@pytest.mark.parametrize("test_value", [0.0, 1.5, -1.5, 100.25, -100.75, 3.14159])
def test_redis_float_model_creation_sanity(test_value):
    # Arrange & Act
    model = SimpleFloatModel(value=test_value)

    # Assert
    assert isinstance(model.value, RedisFloat)
    assert model.value.key == model.key
    assert model.value.field_path == ".value"
    assert model.value.json_path == "$.value"
    assert float(model.value) == test_value


def test_redis_float_inheritance_sanity():
    # Arrange & Act
    model = FloatModel(value=42.5)

    # Assert
    assert isinstance(model.value, RedisFloat)
    assert isinstance(model.value, float)
    assert model.value == 42.5
    assert model.value + 10.5 == 53.0
    assert model.value - 5.25 == 37.25


def test_redis_float_clone_functionality_sanity():
    # Arrange
    model = FloatModel(value=42.5)

    # Act
    cloned_float = model.value.clone()

    # Assert
    assert isinstance(cloned_float, float)
    assert not isinstance(cloned_float, type(model.value))
    assert cloned_float == 42.5


@pytest.mark.parametrize(
    "operations",
    [
        [lambda x: x + 10.5, 53.0],
        [lambda x: x - 8.25, 34.25],
        [lambda x: x * 2.0, 85.0],
        [lambda x: x == 42.5, True],
        [lambda x: x > 40.0, True],
        [lambda x: x < 40.0, False],
        [lambda x: x / 2.0, 21.25],
    ],
)
def test_redis_float_arithmetic_operations_sanity(operations):
    # Arrange
    model = FloatModel(value=42.5)
    operation, expected = operations

    # Act
    result = operation(model.value)

    # Assert
    assert result == expected
