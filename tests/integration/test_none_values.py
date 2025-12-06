import pytest

from tests.models.simple_types import NoneTestModel


@pytest.mark.parametrize(
    "field_name",
    [
        "optional_string",
        "optional_int",
        "optional_bool",
        "optional_bytes",
        "optional_list",
        "optional_dict",
    ],
)
@pytest.mark.asyncio
async def test_none_values_persistence_sanity(field_name):
    # Arrange
    model = NoneTestModel()
    assert getattr(model, field_name) is None

    # Act
    await model.asave()
    retrieved_model = await NoneTestModel.get(model.key)

    # Assert
    assert getattr(retrieved_model, field_name) is None


@pytest.mark.asyncio
async def test_all_none_values_model_persistence_sanity():
    # Arrange
    model = NoneTestModel()

    # Act
    await model.asave()
    retrieved_model = await NoneTestModel.get(model.key)

    # Assert
    assert retrieved_model.optional_string is None
    assert retrieved_model.optional_int is None
    assert retrieved_model.optional_bool is None
    assert retrieved_model.optional_bytes is None
    assert retrieved_model.optional_list is None
    assert retrieved_model.optional_dict is None


@pytest.mark.asyncio
async def test_mixed_none_and_values_persistence_edge_case():
    # Arrange
    model = NoneTestModel(
        optional_string="test",
        optional_int=None,
        optional_bool=True,
        optional_bytes=None,
        optional_list=["item1"],
        optional_dict=None,
    )

    # Act
    await model.asave()
    retrieved_model = await NoneTestModel.get(model.key)

    # Assert
    assert retrieved_model.optional_string == "test"
    assert retrieved_model.optional_int is None
    assert retrieved_model.optional_bool == True
    assert retrieved_model.optional_bytes is None
    assert retrieved_model.optional_list == ["item1"]
    assert retrieved_model.optional_dict is None


@pytest.mark.asyncio
async def test_set_value_to_none_after_initialization_edge_case():
    # Arrange
    model = NoneTestModel(
        optional_string="initial_value",
        optional_int=42,
        optional_list=["item1", "item2"],
    )

    # Act
    model.optional_string = None
    model.optional_int = None
    model.optional_list = None
    await model.asave()
    retrieved_model = await NoneTestModel.get(model.key)

    # Assert
    assert retrieved_model.optional_string is None
    assert retrieved_model.optional_int is None
    assert retrieved_model.optional_list is None
