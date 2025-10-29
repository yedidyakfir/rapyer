import pytest
import pytest_asyncio
from pydantic import Field

from rapyer.base import AtomicRedisModel
from rapyer.types.dct import RedisDict
from rapyer.types.string import RedisStr


class DictModel(AtomicRedisModel):
    data: dict[str, str] = Field(default_factory=dict)
    config: dict[str, int] = Field(default_factory=dict)


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    DictModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize(
    "test_value",
    [
        {"key1": "value1", "key2": "value2"},
        {"name": "test", "type": "example"},
        {},
        {"single": "item"},
    ],
)
@pytest.mark.asyncio
async def test_redis_dict_model_creation_with_initial_value_and_set_load_sanity(
    test_value,
):
    # Arrange
    model = DictModel(data=test_value)

    assert isinstance(model.data, RedisDict)
    assert model.data.redis_key == model.key
    assert model.data.field_path == "data"
    assert model.data.json_path == "$.data"

    # Act - Save and test load operations
    await model.save()

    # Assert - Load and verify
    await model.data.load()
    assert dict(model.data) == test_value

    # Test load from fresh model
    fresh_model = DictModel()
    fresh_model.pk = model.pk
    await fresh_model.data.load()
    assert dict(fresh_model.data) == test_value


@pytest.mark.asyncio
async def test_redis_dict_model_creation_with_dict_operations_sanity():
    # Arrange
    model = DictModel(data={"initial": "value"})

    # Assert model creation
    assert isinstance(model.data, RedisDict)
    assert model.data.json_path == "$.data"
    assert isinstance(model.data["initial"], RedisStr)
    assert model.data["initial"].redis_key == model.key
    assert model.data["initial"].json_path == "$.data.initial"

    # Act - Save and perform dict operations
    await model.save()
    await model.data.aset_item("new_key", "new_value")
    await model.data.aupdate(extra="data")

    # Assert - Load and verify operations worked
    await model.data.load()
    assert model.data["initial"] == "value"
    assert model.data["new_key"] == "new_value"
    assert model.data["extra"] == "data"
