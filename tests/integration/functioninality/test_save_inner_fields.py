import pytest

from tests.models.collection_types import (
    SimpleListModel,
    SimpleDictModel,
    MixedTypesModel,
    ComprehensiveTestModel,
)
from tests.models.complex_types import (
    OuterModel,
    OuterModelWithRedisNested,
    TestRedisModel,
    ComplexNestedModel,
)


@pytest.mark.asyncio
async def test_save_inner_list_field_only_sanity():
    # Arrange
    original_items = ["item1", "item2"]
    updated_items = ["new1", "new2", "new3"]

    model = SimpleListModel(items=original_items)
    await model.save()

    # Modify the model but don't save the entire model
    model.items.extend(updated_items)  # This should NOT be saved

    # Act - Save only the items field with updated data
    await model.items.save()

    # Assert
    retrieved_model = await SimpleListModel.get(model.key)
    assert retrieved_model.items == original_items + updated_items


@pytest.mark.asyncio
async def test_save_inner_list_preserves_other_fields_sanity():
    # Arrange
    original_tags = ["tag1", "tag2"]
    original_metadata = {"key": "value"}
    original_name = "test"
    original_counter = 42

    updated_tags = ["new_tag1", "new_tag2", "new_tag3"]

    model = ComprehensiveTestModel(
        name=original_name,
        counter=original_counter,
        tags=original_tags,
        metadata=original_metadata,
    )
    await model.save()

    # Modify other fields but DON'T save the entire model
    model.name = "should_not_be_saved"
    model.counter = 999
    model.metadata["extra"] = "not_saved"
    model.tags = updated_tags

    # Act - Save only the tag field
    await model.tags.save()

    # Assert
    retrieved_model = await ComprehensiveTestModel.get(model.key)
    assert retrieved_model.tags == updated_tags
    assert retrieved_model.name == original_name  # Should remain unchanged
    assert retrieved_model.counter == original_counter  # Should remain unchanged
    assert retrieved_model.metadata == original_metadata  # Should remain unchanged


@pytest.mark.asyncio
async def test_save_inner_dict_preserves_other_fields_sanity():
    # Arrange
    original_tags = ["tag1", "tag2"]
    original_metadata = {"key": "value"}
    original_name = "test"
    original_counter = 42

    updated_metadata = {"new_key": "new_value", "updated": "data"}

    model = ComprehensiveTestModel(
        name=original_name,
        counter=original_counter,
        tags=original_tags,
        metadata=original_metadata,
    )
    await model.save()

    # Modify other fields but DON'T save the entire model
    model.name = "should_not_be_saved"
    model.counter = 999
    model.tags.append("not_saved")

    # Act - Save only the metadata field
    model.metadata.clear()
    model.metadata.update(updated_metadata)
    await model.metadata.save()

    # Assert
    retrieved_model = await ComprehensiveTestModel.get(model.key)
    assert retrieved_model.metadata == updated_metadata
    assert retrieved_model.name == original_name  # Should remain unchanged
    assert retrieved_model.counter == original_counter  # Should remain unchanged
    assert retrieved_model.tags == original_tags  # Should remain unchanged


@pytest.mark.asyncio
async def test_save_nested_inner_model_field_only_sanity():
    # Arrange
    original_inner_list = ["original1", "original2"]
    original_inner_counter = 5
    original_user_data = {"user1": 100}

    updated_inner_list = ["updated1", "updated2", "updated3"]

    model = OuterModel()
    model.middle_model.inner_model.lst = original_inner_list
    model.middle_model.inner_model.counter = original_inner_counter
    model.user_data = original_user_data
    await model.save()

    # Modify other fields but DON'T save the entire model
    model.middle_model.inner_model.counter = 999  # Should not be saved
    model.user_data["extra"] = 999  # Should not be saved

    # Act - Save only the inner list field
    model.middle_model.inner_model.lst.extend(updated_inner_list)
    await model.middle_model.inner_model.lst.save()

    # Assert
    retrieved_model = await OuterModel.get(model.key)
    assert (
        retrieved_model.middle_model.inner_model.lst
        == original_inner_list + updated_inner_list
    )
    assert retrieved_model.middle_model.inner_model.counter == original_inner_counter
    assert retrieved_model.user_data == original_user_data


@pytest.mark.parametrize(
    "updated_data",
    [
        {"key1": "value1"},
        {"x": "y", "z": "w"},
        {},
    ],
)
@pytest.mark.asyncio
async def test_save_dict_field_parametrized_sanity(updated_data):
    # Arrange
    original_data = {"original_key": "original_value"}

    model = SimpleDictModel(data=original_data)
    await model.save()

    # Act
    model.data.clear()
    model.data.update(updated_data)
    await model.data.save()

    # Assert
    retrieved_model = await SimpleDictModel.get(model.key)
    assert retrieved_model.data == updated_data
