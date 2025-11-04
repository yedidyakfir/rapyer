import pytest

from tests.models.pickle_types import ModelWithUnserializableFields


@pytest.mark.asyncio
async def test_model_with_unserializable_fields__save_and_load__models_equal_sanity():
    # Arrange
    original_model = ModelWithUnserializableFields(model_type=str)

    # Act
    await original_model.save()
    loaded_model = await ModelWithUnserializableFields.get(original_model.key)

    # Assert
    assert loaded_model == original_model
