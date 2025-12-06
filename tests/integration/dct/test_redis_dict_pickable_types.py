import pytest

from rapyer.types import RedisStr
from tests.models.pickle_types import DictPickableTypesModel


@pytest.mark.parametrize(
    ["type_data", "tuple_data", "set_data", "frozenset_data"],
    [
        [
            {"type1": str},
            {"tuple1": ("hello", 42), "tuple2": ("world", 100)},
            {"set1": {"a", "b"}, "set2": {"x", "y", "z"}},
            {"fs1": frozenset([1, 2, 3]), "fs2": frozenset([4, 5])},
        ],
        [
            {"type1": RedisStr},
            {"tuple1": ("single", 1)},
            {"set1": {"one"}},
            {"fs1": frozenset([42])},
        ],
    ],
)
@pytest.mark.asyncio
async def test_redis_dict_pickable_types_save_load_sanity(
    type_data, tuple_data, set_data, frozenset_data
):
    # Arrange
    model = DictPickableTypesModel(
        type_dict=type_data,
        tuple_dict=tuple_data,
        set_dict=set_data,
        frozenset_dict=frozenset_data,
    )

    # Act
    await model.asave()
    loaded_model = await DictPickableTypesModel.get(model.key)

    # Assert
    assert model == loaded_model
    assert loaded_model.type_dict == type_data
    assert loaded_model.tuple_dict == tuple_data
    assert loaded_model.set_dict == set_data
    assert loaded_model.frozenset_dict == frozenset_data
