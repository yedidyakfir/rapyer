import base64

import pytest
import pytest_asyncio

from redis_pydantic.base import BaseRedisModel
from redis_pydantic.types import ALL_TYPES


class BytesModel(BaseRedisModel):
    data: bytes = b""
    binary_content: bytes = b"default"

    class Meta:
        redis = None
        redis_type = ALL_TYPES


@pytest_asyncio.fixture
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
async def test_redis_bytes_set_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = BytesModel()
    await model.save()

    # Act
    await model.data.set(test_values)

    # Assert
    redis_value = await real_redis_client.json().get(model.key, model.data.json_path)
    expected_encoded = base64.b64encode(test_values).decode()
    assert redis_value == expected_encoded


@pytest.mark.parametrize(
    "test_values", [b"hello", b"world", b"", b"\x00\x01\x02\x03", b"\xff\xfe\xfd"]
)
@pytest.mark.asyncio
async def test_redis_bytes_load_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = BytesModel()
    await model.save()
    encoded_value = base64.b64encode(test_values).decode()
    await real_redis_client.json().set(model.key, model.data.json_path, encoded_value)

    # Act
    loaded_value = await model.data.load()

    # Assert
    assert loaded_value == test_values


@pytest.mark.asyncio
async def test_redis_bytes_load_with_none_value_edge_case(real_redis_client):
    # Arrange
    model = BytesModel()
    await model.save()

    # Act
    loaded_value = await model.data.load()

    # Assert
    assert loaded_value == b""


@pytest.mark.parametrize(
    "redis_values",
    [
        ("string_value", b"string_value"),
        (b"actual_bytes", b"actual_bytes"),
        (42, b"42"),
    ],
)
@pytest.mark.asyncio
async def test_redis_bytes_load_type_conversion_edge_case(
    real_redis_client, redis_values
):
    # Arrange
    redis_value, expected = redis_values
    model = BytesModel(data=redis_value)
    await model.save()

    # Act
    loaded_value = await model.data.load()

    # Assert
    assert loaded_value == expected


@pytest.mark.parametrize(
    "operations",
    [
        (lambda x: len(x), 5),
        (lambda x: x[1:3], b"el"),
        (lambda x: x + b" world", b"hello world"),
        (lambda x: b"ell" in x, True),
        (lambda x: x.decode(), "hello"),
        (lambda x: x.upper(), b"HELLO"),
        (lambda x: x.replace(b"l", b"x"), b"hexxo"),
    ],
)
@pytest.mark.asyncio
async def test_redis_bytes_operations_sanity(real_redis_client, operations):
    # Arrange
    model = BytesModel(data=b"hello")
    operation, expected = operations

    # Act
    result = operation(model.data)

    # Assert
    assert result == expected
