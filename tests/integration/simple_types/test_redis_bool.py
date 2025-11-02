import pytest

from tests.models.simple_types import BoolModel


@pytest.mark.asyncio
async def test_redis_bool_truthy_values_functionality_sanity():
    # Arrange
    model = BoolModel(is_active=True)

    # Act & Assert
    assert model.is_active
