import pytest

from tests.models.functionality_types import LockUpdateTestModel as LockTestModel


@pytest.mark.asyncio
async def test_lock_context_manager_updates_model_with_new_data_sanity():
    # Arrange
    original_model = LockTestModel(name="test", value=42, tags=["tag1"])
    await original_model.save()

    # Act
    new_model = await LockTestModel.get(original_model.key)
    new_model.name = "updated_name"
    new_model.value = 100
    new_model.tags.append("tag2")
    await new_model.save()

    # Assert
    async with original_model.lock() as locked_model:
        validated_lock_model = LockTestModel.model_validate(locked_model.model_dump())
        validated_original_model = LockTestModel.model_validate(
            original_model.model_dump()
        )
        assert (
            validated_lock_model
            == validated_original_model
            == original_model
            == locked_model
        )
        for field_name, field_info in LockTestModel.model_fields.items():
            original_field = getattr(original_model, field_name)
            locked_field = getattr(locked_model, field_name)
            assert (
                locked_field.json_path == original_field.json_path == f"$.{field_name}"
            )
