import pytest

from tests.models.simple_types import StrModel


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
    model.name = test_values
    await model.name.save()

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
    model.name = test_values
    await model.name.save()

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
    with pytest.raises(ValueError, match="Input should be a valid string"):
        model.name = 42


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
async def test_redis_str_persistence_across_instances_edge_case():
    # Arrange
    model1 = StrModel(name="original")
    await model1.save()
    model1.name = "modified"
    await model1.name.save()

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
    model.name = ""
    await model.name.save()

    # Assert
    fresh_model = StrModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.name.load()
    assert loaded_value == ""
    assert len(model.name) == 0
