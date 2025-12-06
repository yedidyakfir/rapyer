import pytest

from tests.models.pickle_types import ListPickableTypesModel


@pytest.mark.parametrize(
    ["type_data", "tuple_data", "set_data", "frozenset_data", "nested_list"],
    [
        [
            [str, int, list],
            [("hello", 42), ("world", 100), ("test", 1)],
            [{"a", "b"}, {"x", "y", "z"}],
            [frozenset([1, 2, 3]), frozenset([4, 5])],
            [],
        ],
        [[str, type], [("single", 1)], [{"one"}], [frozenset([42])], [[str, int]]],
    ],
)
@pytest.mark.asyncio
async def test_redis_list_pickable_types_save_load_sanity(
    type_data, tuple_data, set_data, frozenset_data, nested_list
):
    # Arrange
    model = ListPickableTypesModel(
        type_list=type_data,
        tuple_list=tuple_data,
        set_list=set_data,
        frozenset_list=frozenset_data,
        nested_list=nested_list,
    )

    # Act
    await model.asave()
    loaded_model = await ListPickableTypesModel.get(model.key)

    # Assert
    assert model == loaded_model
    assert loaded_model.type_list == type_data
    assert loaded_model.tuple_list == tuple_data
    assert loaded_model.set_list == set_data
    assert loaded_model.frozenset_list == frozenset_data
    assert loaded_model.nested_list == nested_list
