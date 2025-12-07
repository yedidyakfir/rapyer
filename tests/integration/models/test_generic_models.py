import pytest

from tests.models.generic_types import GenericListModel, GenericDictModel


@pytest.mark.asyncio
async def test_generic_list_model_with_string_values__save_and_get__check_data_persisted():
    # Arrange
    model = GenericListModel[str](items=["item1", "item2", "item3"], name="test_model")

    # Act
    await model.asave()
    loaded_model = await GenericListModel[str].aget(model.key)

    # Assert
    assert loaded_model == model


@pytest.mark.asyncio
async def test_generic_list_model_with_int_values__save_and_get__check_data_persisted():
    # Arrange
    model = GenericListModel[int](items=[1, 2, 3, 4], name="int_model")

    # Act
    await model.asave()
    loaded_model = await GenericListModel[int].aget(model.key)

    # Assert
    assert loaded_model == model


@pytest.mark.asyncio
async def test_generic_dict_model_with_string_values__save_and_get__check_data_persisted():
    # Arrange
    model = GenericDictModel[str](
        data={"key1": "value1", "key2": "value2"},
        metadata={"type": "test", "version": "1.0"},
    )

    # Act
    await model.asave()
    loaded_model = await GenericDictModel[str].aget(model.key)

    # Assert
    assert loaded_model == model


@pytest.mark.asyncio
async def test_generic_list_model__ainsert_operation__check_redis_insert():
    # Arrange
    model = GenericListModel[str](items=["first", "third"], name="insert_test")
    await model.asave()

    # Act
    await model.items.ainsert(1, "second")

    # Assert
    loaded_model = await GenericListModel[str].aget(model.key)
    assert loaded_model.items == ["first", "second", "third"]


@pytest.mark.asyncio
async def test_generic_list_model__aappend_operation__check_redis_append():
    # Arrange
    model = GenericListModel[str](items=["item1", "item2"], name="append_test")
    await model.asave()

    # Act
    await model.items.aappend("item3")

    # Assert
    loaded_model = await GenericListModel[str].aget(model.key)
    assert loaded_model.items == ["item1", "item2", "item3"]


@pytest.mark.asyncio
async def test_generic_list_model__aextend_operation__check_redis_extend():
    # Arrange
    model = GenericListModel[str](items=["item1"], name="extend_test")
    await model.asave()

    # Act
    await model.items.aextend(["item2", "item3"])

    # Assert
    loaded_model = await GenericListModel[str].aget(model.key)
    assert set(loaded_model.items) == {"item1", "item2", "item3"}
    assert len(loaded_model.items) == 3


@pytest.mark.asyncio
async def test_generic_list_model__aclear_operation__check_redis_clear():
    # Arrange
    model = GenericListModel[str](items=["item1", "item2", "item3"], name="clear_test")
    await model.asave()

    # Act
    await model.items.aclear()

    # Assert
    loaded_model = await GenericListModel[str].aget(model.key)
    assert loaded_model.items == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_data", [["string1", "string2"], [1, 2, 3], [True, False, True]]
)
async def test_generic_list_model_parameterized__save_and_load__check_data_types_preserved(
    test_data,
):
    # Arrange
    model = GenericListModel(items=test_data, name="param_test")

    # Act
    await model.asave()
    loaded_model = await GenericListModel.aget(model.key)

    # Assert
    assert loaded_model.items == test_data
    assert loaded_model.name == "param_test"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_data",
    [
        {"key1": "value1", "key2": "value2"},
        {"num1": 100, "num2": 200},
        {"flag1": True, "flag2": False},
    ],
)
async def test_generic_dict_model_parameterized__save_and_load__check_data_types_preserved(
    test_data,
):
    # Arrange
    model = GenericDictModel(data=test_data, metadata={"test": "true"})

    # Act
    await model.asave()
    loaded_model = await GenericDictModel.aget(model.key)

    # Assert
    assert loaded_model.data == test_data
    assert loaded_model.metadata == {"test": "true"}


@pytest.mark.asyncio
async def test_generic_model__delete_operation__check_key_removed(real_redis_client):
    # Arrange
    model = GenericListModel[str](items=["test"], name="delete_test")
    await model.asave()

    # Act
    await model.adelete()

    # Assert
    key_exists = await real_redis_client.exists(model.key)
    assert key_exists == 0


@pytest.mark.asyncio
async def test_generic_model__try_delete_existing__check_returns_true():
    # Arrange
    model = GenericListModel[str](items=["test"], name="try_delete_test")
    await model.asave()

    # Act
    result = await GenericListModel.adelete_by_key(model.key)

    # Assert
    assert result is True


@pytest.mark.asyncio
async def test_generic_model__try_delete_nonexistent__check_returns_false():
    # Arrange
    mock_key = "GenericListModel:nonexistent_key"

    # Act
    result = await GenericListModel.adelete_by_key(mock_key)

    # Assert
    assert result is False
