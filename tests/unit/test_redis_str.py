import pytest
import pytest_asyncio

from redis_pydantic.base import BaseRedisModel
from redis_pydantic.types import ALL_TYPES


class StrModel(BaseRedisModel):
    name: str = ""
    description: str = "default"

    class Meta:
        redis = None
        redis_type = ALL_TYPES


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    StrModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize(
    "test_values", ["hello", "world", "", "special chars: !@#$%", "unicode: 你好"]
)
@pytest.mark.asyncio
async def test_redis_str_set_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = StrModel()

    # Act
    await model.name.set(test_values)

    # Assert
    redis_value = await real_redis_client.json().get(model.key, model.name.json_path)
    assert redis_value == test_values


@pytest.mark.parametrize(
    "test_values", ["hello", "world", "", "special chars: !@#$%", "unicode: 你好"]
)
@pytest.mark.asyncio
async def test_redis_str_load_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = StrModel()
    await real_redis_client.json().set(model.key, model.name.json_path, test_values)

    # Act
    loaded_value = await model.name.load()

    # Assert
    assert loaded_value == test_values


@pytest.mark.asyncio
async def test_redis_str_load_with_none_value_edge_case(real_redis_client):
    # Arrange
    model = StrModel()

    # Act
    loaded_value = await model.name.load()

    # Assert
    assert loaded_value == ""


@pytest.mark.parametrize("redis_values", [b"bytes_value", 42, True, None])
@pytest.mark.asyncio
async def test_redis_str_load_type_conversion_edge_case(
    real_redis_client, redis_values
):
    # Arrange
    model = StrModel()
    await real_redis_client.json().set(model.key, model.name.json_path, redis_values)

    # Act
    loaded_value = await model.name.load()

    # Assert
    if redis_values == b"bytes_value":
        assert loaded_value == "bytes_value"
    elif redis_values == 42:
        assert loaded_value == "42"
    elif redis_values == True:
        assert loaded_value == "True"
    elif redis_values is None:
        assert loaded_value == "None"


@pytest.mark.asyncio
async def test_redis_str_set_with_wrong_type_edge_case(real_redis_client):
    # Arrange
    model = StrModel()

    # Act & Assert
    with pytest.raises(TypeError, match="Value must be str"):
        await model.name.set(42)


@pytest.mark.asyncio
async def test_redis_str_inheritance_sanity(real_redis_client):
    # Arrange & Act
    model = StrModel(name="hello")

    # Assert
    from redis_pydantic.types.string import RedisStr

    assert isinstance(model.name, RedisStr)
    assert isinstance(model.name, str)
    assert model.name == "hello"
    assert model.name + " world" == "hello world"
    assert len(model.name) == 5


@pytest.mark.asyncio
async def test_redis_str_clone_functionality_sanity(real_redis_client):
    # Arrange
    model = StrModel(name="test")

    # Act
    cloned_str = model.name.clone()

    # Assert
    assert isinstance(cloned_str, str)
    assert not isinstance(cloned_str, type(model.name))
    assert cloned_str == "test"


@pytest.mark.asyncio
async def test_redis_str_model_creation_functionality_sanity(real_redis_client):
    # Arrange & Act
    model = StrModel(name="test")

    # Assert
    from redis_pydantic.types.string import RedisStr

    assert isinstance(model.name, RedisStr)
    assert hasattr(model.name, "redis_key")
    assert hasattr(model.name, "field_path")
    assert hasattr(model.name, "redis")
    assert hasattr(model.name, "json_path")
    assert model.name.redis_key == model.key
    assert model.name.field_path == "name"
    assert model.name.json_path == "$.name"
    assert model.name.redis == real_redis_client


@pytest.mark.asyncio
async def test_redis_str_persistence_across_instances_edge_case(real_redis_client):
    # Arrange
    model1 = StrModel(name="original")
    await model1.name.set("modified")

    # Act
    model2 = StrModel()
    model2.pk = model1.pk
    loaded_value = await model2.name.load()

    # Assert
    assert loaded_value == "modified"


@pytest.mark.parametrize(
    "operations",
    [
        (lambda x: x.upper(), "HELLO"),
        (lambda x: x.lower(), "hello"),
        (lambda x: x.strip(), "hello"),
        (lambda x: len(x), 5),
        (lambda x: x[1:3], "el"),
        (lambda x: "ell" in x, True),
        (lambda x: x.split("l"), ["he", "", "o"]),
    ],
)
@pytest.mark.asyncio
async def test_redis_str_string_operations_sanity(real_redis_client, operations):
    # Arrange
    model = StrModel(name="hello")
    operation, expected = operations

    # Act
    result = operation(model.name)

    # Assert
    assert result == expected


@pytest.mark.asyncio
async def test_redis_str_concatenation_functionality_sanity(real_redis_client):
    # Arrange
    model = StrModel(name="hello")

    # Act & Assert
    assert model.name + " world" == "hello world"
    assert "prefix " + model.name == "prefix hello"


@pytest.mark.asyncio
async def test_redis_str_empty_string_functionality_edge_case(real_redis_client):
    # Arrange
    model = StrModel(name="")

    # Act
    await model.name.set("")

    # Assert
    redis_value = await real_redis_client.json().get(model.key, model.name.json_path)
    assert redis_value == ""
    assert len(model.name) == 0
