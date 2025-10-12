import pytest
import pytest_asyncio
from pydantic import Field

from redis_pydantic.base import BaseRedisModel


class IntListModel(BaseRedisModel):
    items: list[int] = Field(default_factory=list)


class StrListModel(BaseRedisModel):
    items: list[str] = Field(default_factory=list)


class DictListModel(BaseRedisModel):
    items: list[dict[str, str]] = Field(default_factory=list)


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    IntListModel.Meta.redis = redis_client
    StrListModel.Meta.redis = redis_client
    DictListModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize("model_class,test_value", [
    [IntListModel, 42],
    [StrListModel, "test_string"],
    [DictListModel, {"key": "value"}],
])
@pytest.mark.asyncio
async def test_redis_list_setitem_type_checking_sanity(real_redis_client, model_class, test_value):
    # Arrange
    model = model_class()
    if isinstance(test_value, int):
        model.items = [0, 0, 0]
    elif isinstance(test_value, str):
        model.items = ["", "", ""]
    elif isinstance(test_value, dict):
        model.items = [{}, {}, {}]
    await model.save()

    # Act
    model.items[2] = test_value

    # Assert
    from redis_pydantic.types.integer import RedisInt
    from redis_pydantic.types.string import RedisStr
    from redis_pydantic.types.dct import RedisDict

    if isinstance(test_value, int):
        assert isinstance(model.items[2], RedisInt)
    elif isinstance(test_value, str):
        assert isinstance(model.items[2], RedisStr)
    elif isinstance(test_value, dict):
        assert isinstance(model.items[2], RedisDict)


@pytest.mark.parametrize("index,test_value", [
    [0, 100],
    [1, 200],
    [2, 300],
])
@pytest.mark.asyncio
async def test_redis_list_setitem_int_operations_sanity(real_redis_client, index, test_value):
    # Arrange
    model = IntListModel(items=[0, 0, 0])
    await model.save()
    
    # Act
    model.items[index] = test_value
    await model.items[index].set(test_value + 50)

    # Assert
    fresh_model = IntListModel()
    fresh_model.pk = model.pk
    await fresh_model.items.load()
    # After loading, items are regular Python types, not Redis types
    assert fresh_model.items[index] == test_value + 50


@pytest.mark.parametrize("index,test_value", [
    [0, "hello"],
    [1, "world"],
    [2, "test"],
])
@pytest.mark.asyncio
async def test_redis_list_setitem_str_operations_sanity(real_redis_client, index, test_value):
    # Arrange
    model = StrListModel(items=["", "", ""])
    await model.save()
    
    # Act
    model.items[index] = test_value
    await model.items[index].set(test_value + "_modified")

    # Assert
    fresh_model = StrListModel()
    fresh_model.pk = model.pk
    await fresh_model.items.load()
    # After loading, items are regular Python types, not Redis types
    assert fresh_model.items[index] == test_value + "_modified"


@pytest.mark.parametrize("index,test_value", [
    [0, {"key1": "value1"}],
    [1, {"key2": "value2"}],
    [2, {"key3": "value3"}],
])
@pytest.mark.asyncio
async def test_redis_list_setitem_dict_operations_sanity(real_redis_client, index, test_value):
    # Arrange
    model = DictListModel(items=[{}, {}, {}])
    await model.save()
    
    # Act
    model.items[index] = test_value
    await model.save()  # Save current state to Redis before update
    await model.items[index].aupdate(**{"new_key": "new_value"})

    # Assert
    fresh_model = DictListModel()
    fresh_model.pk = model.pk
    await fresh_model.items.load()
    # After loading, items are regular Python types, not Redis types
    expected_dict = {**test_value, "new_key": "new_value"}
    assert fresh_model.items[index] == expected_dict


@pytest.mark.asyncio
async def test_redis_list_setitem_int_arithmetic_operations_sanity(real_redis_client):
    # Arrange
    model = IntListModel(items=[0, 0, 0])
    await model.save()
    
    # Act
    model.items[1] = 50

    # Assert
    assert model.items[1] + 10 == 60
    assert model.items[1] - 5 == 45
    assert model.items[1] * 2 == 100
    assert model.items[1] == 50


@pytest.mark.asyncio
async def test_redis_list_setitem_str_operations_edge_case(real_redis_client):
    # Arrange
    model = StrListModel(items=["", "", ""])
    await model.save()
    
    # Act
    model.items[0] = "test"

    # Assert
    assert model.items[0] + "_suffix" == "test_suffix"
    assert model.items[0].upper() == "TEST"
    assert len(model.items[0]) == 4


@pytest.mark.asyncio
async def test_redis_list_setitem_dict_key_access_edge_case(real_redis_client):
    # Arrange
    model = DictListModel(items=[{}, {}, {}])
    await model.save()
    
    # Act
    model.items[2] = {"test_key": "test_value", "another_key": "another_value"}

    # Assert
    assert model.items[2]["test_key"] == "test_value"
    assert model.items[2]["another_key"] == "another_value"
    assert len(model.items[2]) == 2


@pytest.mark.asyncio
async def test_redis_list_setitem_redis_field_paths_sanity(real_redis_client):
    # Arrange
    model = IntListModel(items=[0, 0, 0])
    await model.save()
    
    # Act
    model.items[1] = 42

    # Assert
    assert model.items[1].redis_key == model.key
    assert model.items[1].field_path == "items[1]"
    assert model.items[1].json_path == "$.items[1]"


@pytest.mark.asyncio
async def test_redis_list_setitem_multiple_indices_sanity(real_redis_client):
    # Arrange
    model = IntListModel(items=[0, 0, 0, 0, 0])
    await model.save()
    
    # Act
    model.items[0] = 10
    model.items[2] = 20
    model.items[4] = 30

    # Assert
    assert model.items[0] == 10
    assert model.items[1] == 0
    assert model.items[2] == 20
    assert model.items[3] == 0
    assert model.items[4] == 30


@pytest.mark.asyncio
async def test_redis_list_setitem_persistence_across_instances_edge_case(real_redis_client):
    # Arrange
    model1 = IntListModel(items=[1, 2, 3])
    await model1.save()
    
    # Act
    model1.items[1] = 99
    await model1.items[1].set(99)
    
    # Assert
    model2 = IntListModel()
    model2.pk = model1.pk
    await model2.items.load()
    # After loading, items are regular Python types, not Redis types
    assert model2.items[1] == 99