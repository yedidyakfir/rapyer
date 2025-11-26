from typing import Any

import pytest

from tests.models.pickle_types import ModelWithUnserializableFields


@pytest.mark.parametrize(
    "test_data",
    [
        {
            "model_type": str,
            "callable_field": type,
            "python_type": ModelWithUnserializableFields,
            "value": 42,
        },
        {"model_type": str, "callable_field": list, "python_type": str, "value": 100},
        {"model_type": str, "callable_field": tuple, "python_type": int, "value": 0},
        {
            "model_type": None,
            "callable_field": type,
            "python_type": ModelWithUnserializableFields,
            "value": 42,
        },
        {
            "model_type": str,
            "callable_field": None,
            "python_type": ModelWithUnserializableFields,
            "value": 42,
        },
        {"model_type": str, "callable_field": type, "python_type": None, "value": 42},
        {
            "model_type": str,
            "callable_field": type,
            "python_type": ModelWithUnserializableFields,
            "value": None,
        },
        {
            "model_type": None,
            "callable_field": None,
            "python_type": None,
            "value": None,
        },
    ],
)
@pytest.mark.asyncio
async def test_model_with_unserializable_fields__save_and_load__models_equal_sanity(
    test_data,
):
    # Arrange
    original_model = ModelWithUnserializableFields(**test_data)

    # Act
    await original_model.save()
    loaded_model = await ModelWithUnserializableFields.get(original_model.key)

    # Assert
    assert loaded_model == original_model
    assert loaded_model.model_type == original_model.model_type
    assert loaded_model.callable_field == original_model.callable_field
    assert loaded_model.python_type == original_model.python_type
    assert loaded_model.value == original_model.value


@pytest.mark.asyncio
async def test_model_with_unserializable_fields__none_fields_preserved__edge_case():
    # Arrange
    original_model = ModelWithUnserializableFields(
        model_type=None, callable_field=None, python_type=None, value=None
    )

    # Act
    await original_model.save()
    loaded_model = await ModelWithUnserializableFields.get(original_model.key)

    # Assert
    assert loaded_model.model_type is None
    assert loaded_model.callable_field is None
    assert loaded_model.python_type is None
    assert loaded_model.value is None


@pytest.mark.parametrize(
    "field_values",
    [
        {"callable_field": complex, "value": 314},
        {"callable_field": frozenset, "value": -1},
        {"callable_field": bytes, "value": 999},
        {"callable_field": range, "value": 123},
    ],
)
@pytest.mark.asyncio
async def test_model_with_unserializable_fields__complex_types__edge_case(field_values):
    # Arrange
    original_model = ModelWithUnserializableFields(**field_values)

    # Act
    await original_model.save()
    loaded_model = await ModelWithUnserializableFields.get(original_model.key)

    # Assert
    assert loaded_model == original_model
    for field_name, expected_value in field_values.items():
        assert getattr(loaded_model, field_name) == expected_value


@pytest.mark.asyncio
async def test_model_with_unserializable_fields__update_none_fields__edge_case():
    # Arrange
    original_model = ModelWithUnserializableFields(model_type=str, value=42)
    await original_model.save()

    # Act
    original_model.model_type = None
    original_model.value = None
    await original_model.save()
    loaded_model = await ModelWithUnserializableFields.get(original_model.key)

    # Assert
    assert loaded_model.model_type is None
    assert loaded_model.value is None
    assert loaded_model.callable_field == type  # Should preserve default
    assert loaded_model.python_type == Any  # Should preserve default
