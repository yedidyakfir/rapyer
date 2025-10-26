import pytest
import pytest_asyncio

from rapyer.base import AtomicRedisModel


class BytesModel(AtomicRedisModel):
    data: bytes = b""
    binary_content: bytes = b"default"


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    BytesModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.parametrize(
    "test_values",
    [
        b"hello",
        b"world",
        b"",
        b"\x00\x01\x02\x03",
        b"\xff\xfe\xfd",
        b"unicode bytes: \xc4\x85\xc4\x99",
    ],
)
@pytest.mark.asyncio
async def test_redis_bytes_set_functionality_sanity(test_values):
    # Arrange
    model = BytesModel()
    await model.save()

    # Act
    await model.data.set(test_values)

    # Assert
    fresh_model = BytesModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.data.load()
    assert loaded_value == test_values


@pytest.mark.parametrize(
    "test_values", [b"hello", b"world", b"", b"\x00\x01\x02\x03", b"\xff\xfe\xfd"]
)
@pytest.mark.asyncio
async def test_redis_bytes_load_functionality_sanity(test_values):
    # Arrange
    model = BytesModel()
    await model.save()
    await model.data.set(test_values)

    # Act
    fresh_model = BytesModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.data.load()

    # Assert
    assert loaded_value == test_values


@pytest.mark.asyncio
async def test_redis_bytes_load_with_none_value_edge_case():
    # Arrange
    model = BytesModel()
    await model.save()

    # Act
    loaded_value = await model.data.load()

    # Assert
    assert loaded_value == b""


@pytest.mark.parametrize(
    ["redis_values"],
    [
        [b"string_value", b"string_value"],
        [b"actual_bytes", b"actual_bytes"],
        [b"42", b"42"],
    ],
)
@pytest.mark.asyncio
async def test_redis_bytes_load_type_conversion_edge_case(redis_values):
    # Arrange
    redis_value, expected = redis_values
    model = BytesModel()
    await model.save()
    await model.data.set(redis_value)

    # Act
    fresh_model = BytesModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.data.load()

    # Assert
    assert loaded_value == expected


@pytest.mark.parametrize(
    ["operations"],
    [
        [lambda x: len(x), 5],
        [lambda x: x[1:3], b"el"],
        [lambda x: x + b" world", b"hello world"],
        [lambda x: b"ell" in x, True],
        [lambda x: x.decode(), "hello"],
        [lambda x: x.upper(), b"HELLO"],
        [lambda x: x.replace(b"l", b"x"), b"hexxo"],
    ],
)
@pytest.mark.asyncio
async def test_redis_bytes_operations_sanity(operations):
    # Arrange
    model = BytesModel(data=b"hello")
    operation, expected = operations

    # Act
    result = operation(model.data)

    # Assert
    assert result == expected
