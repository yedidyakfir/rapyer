import pytest
import pytest_asyncio

from rapyer.base import AtomicRedisModel


class StrModel(AtomicRedisModel):
    name: str = ""
    description: str = "default"


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    StrModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize(
    "test_values",
    ["hello", "world", "", "special chars: !@#$%", "unicode: 你好"],
)
@pytest.mark.asyncio
async def test_redis_str_set_functionality_sanity(test_values):
    # Arrange
    model = StrModel()
    await model.save()

    # Act
    await model.name.set(test_values)

    # Assert
    fresh_model = StrModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.name.load()
    assert loaded_value == test_values


@pytest.mark.parametrize(
    "test_values",
    ["hello", "world", "", "special chars: !@#$%", "unicode: 你好"],
)
@pytest.mark.asyncio
async def test_redis_str_load_functionality_sanity(test_values):
    # Arrange
    model = StrModel()
    await model.save()
    await model.name.set(test_values)

    # Act
    fresh_model = StrModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.name.load()

    # Assert
    assert loaded_value == test_values


@pytest.mark.asyncio
async def test_redis_str_load_with_none_value_edge_case():
    # Arrange
    model = StrModel()

    # Act
    loaded_value = await model.name.load()

    # Assert
    assert loaded_value is None


@pytest.mark.asyncio
async def test_redis_str_set_with_wrong_type_edge_case():
    # Arrange
    model = StrModel()

    # Act & Assert
    with pytest.raises(TypeError, match="Value must be str"):
        await model.name.set(42)


@pytest.mark.asyncio
async def test_redis_str_inheritance_sanity():
    # Arrange & Act
    model = StrModel(name="hello")

    # Assert
    from rapyer.types.string import RedisStr

    assert isinstance(model.name, RedisStr)
    assert isinstance(model.name, str)
    assert model.name == "hello"
    assert model.name + " world" == "hello world"
    assert len(model.name) == 5


@pytest.mark.asyncio
async def test_redis_str_clone_functionality_sanity():
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
    from rapyer.types.string import RedisStr

    assert isinstance(model.name, RedisStr)
    assert hasattr(model.name, "key")
    assert hasattr(model.name, "field_path")
    assert hasattr(model.name, "redis")
    assert hasattr(model.name, "json_path")
    assert model.name.key == model.key
    assert model.name.field_path == "name"
    assert model.name.json_path == "$.name"
    assert model.name.redis == real_redis_client


@pytest.mark.asyncio
async def test_redis_str_persistence_across_instances_edge_case():
    # Arrange
    model1 = StrModel(name="original")
    await model1.save()
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
        [lambda x: x.upper(), "HELLO"],
        [lambda x: x.lower(), "hello"],
        [lambda x: x.strip(), "hello"],
        [lambda x: len(x), 5],
        [lambda x: x[1:3], "el"],
        [lambda x: "ell" in x, True],
        [lambda x: x.split("l"), ["he", "", "o"]],
    ],
)
@pytest.mark.asyncio
async def test_redis_str_string_operations_sanity(operations):
    # Arrange
    model = StrModel(name="hello")
    operation, expected = operations

    # Act
    result = operation(model.name)

    # Assert
    assert result == expected


@pytest.mark.asyncio
async def test_redis_str_concatenation_functionality_sanity():
    # Arrange
    model = StrModel(name="hello")

    # Act & Assert
    assert model.name + " world" == "hello world"
    assert "prefix " + model.name == "prefix hello"


@pytest.mark.asyncio
async def test_redis_str_empty_string_functionality_edge_case():
    # Arrange
    model = StrModel(name="")
    await model.save()

    # Act
    await model.name.set("")

    # Assert
    fresh_model = StrModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.name.load()
    assert loaded_value == ""
    assert len(model.name) == 0
