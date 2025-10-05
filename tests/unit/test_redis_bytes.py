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
    model = BytesModel()
    await real_redis_client.json().set(model.key, model.data.json_path, redis_value)

    # Act
    loaded_value = await model.data.load()

    # Assert
    assert loaded_value == expected


@pytest.mark.asyncio
async def test_redis_bytes_load_invalid_base64_edge_case(real_redis_client):
    # Arrange
    model = BytesModel()
    await real_redis_client.json().set(
        model.key, model.data.json_path, "invalid_base64!"
    )

    # Act
    loaded_value = await model.data.load()

    # Assert
    assert loaded_value == b"invalid_base64!"


@pytest.mark.asyncio
async def test_redis_bytes_set_with_wrong_type_edge_case(real_redis_client):
    # Arrange
    model = BytesModel()

    # Act & Assert
    with pytest.raises(TypeError, match="Value must be bytes"):
        await model.data.set("not bytes")


@pytest.mark.asyncio
async def test_redis_bytes_inheritance_sanity(real_redis_client):
    # Arrange & Act
    model = BytesModel(data=b"hello")

    # Assert
    from redis_pydantic.types.byte import RedisBytes

    assert isinstance(model.data, RedisBytes)
    assert isinstance(model.data, bytes)
    assert model.data == b"hello"
    assert model.data + b" world" == b"hello world"
    assert len(model.data) == 5


@pytest.mark.asyncio
async def test_redis_bytes_clone_functionality_sanity(real_redis_client):
    # Arrange
    model = BytesModel(data=b"test")

    # Act
    cloned_bytes = model.data.clone()

    # Assert
    assert isinstance(cloned_bytes, bytes)
    assert not isinstance(cloned_bytes, type(model.data))
    assert cloned_bytes == b"test"


@pytest.mark.asyncio
async def test_redis_bytes_model_creation_functionality_sanity(real_redis_client):
    # Arrange & Act
    model = BytesModel(data=b"test")

    # Assert
    from redis_pydantic.types.byte import RedisBytes

    assert isinstance(model.data, RedisBytes)
    assert hasattr(model.data, "redis_key")
    assert hasattr(model.data, "field_path")
    assert hasattr(model.data, "redis")
    assert hasattr(model.data, "json_path")
    assert model.data.redis_key == model.key
    assert model.data.field_path == "data"
    assert model.data.json_path == "$.data"
    assert model.data.redis == real_redis_client


@pytest.mark.asyncio
async def test_redis_bytes_persistence_across_instances_edge_case(real_redis_client):
    # Arrange
    model1 = BytesModel(data=b"original")
    await model1.data.set(b"modified")

    # Act
    model2 = BytesModel()
    model2.pk = model1.pk
    loaded_value = await model2.data.load()

    # Assert
    assert loaded_value == b"modified"


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


@pytest.mark.asyncio
async def test_redis_bytes_concatenation_functionality_sanity(real_redis_client):
    # Arrange
    model = BytesModel(data=b"hello")

    # Act & Assert
    assert model.data + b" world" == b"hello world"
    assert b"prefix " + model.data == b"prefix hello"


@pytest.mark.asyncio
async def test_redis_bytes_empty_bytes_functionality_edge_case(real_redis_client):
    # Arrange
    model = BytesModel(data=b"")

    # Act
    await model.data.set(b"")

    # Assert
    redis_value = await real_redis_client.json().get(model.key, model.data.json_path)
    expected_encoded = base64.b64encode(b"").decode()
    assert redis_value == expected_encoded
    assert len(model.data) == 0


@pytest.mark.asyncio
async def test_redis_bytes_binary_data_functionality_sanity(real_redis_client):
    # Arrange
    binary_data = bytes(range(256))  # All possible byte values
    model = BytesModel()

    # Act
    await model.data.set(binary_data)
    loaded_value = await model.data.load()

    # Assert
    assert loaded_value == binary_data
    assert len(loaded_value) == 256


@pytest.mark.asyncio
async def test_redis_bytes_creation_from_string_functionality_edge_case(
    real_redis_client,
):
    # Arrange & Act
    model = BytesModel(data="string")  # This should be converted to bytes

    # Assert
    # The model should handle string input by converting to bytes in __new__
    assert isinstance(model.data, bytes)
