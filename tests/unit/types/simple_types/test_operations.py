from unittest.mock import AsyncMock, MagicMock

import pytest

from rapyer.base import AtomicRedisModel
from rapyer.types.boolean import RedisBool
from rapyer.types.byte import RedisBytes
from rapyer.types.integer import RedisInt
from rapyer.types.string import RedisStr


class SimpleStringModel(AtomicRedisModel):
    name: str


class SimpleIntModel(AtomicRedisModel):
    count: int


class SimpleBoolModel(AtomicRedisModel):
    flag: bool


class SimpleBytesModel(AtomicRedisModel):
    data: bytes


@pytest.mark.parametrize(
    "initial_value,new_value", [("hello", "world"), ("", "test"), ("old", "new")]
)
def test_redis_str_operations_sanity(initial_value, new_value):
    # Arrange
    model = SimpleStringModel(name=initial_value)
    mock_redis = MagicMock()
    mock_redis.json().set = AsyncMock()
    model.name._base_model_link = model
    model.name.client = mock_redis

    # Act - Test assignment
    model.name = new_value

    # Assert
    assert isinstance(model.name, RedisStr)
    assert str(model.name) == new_value
    assert model.name.key == model.key


@pytest.mark.parametrize(
    "initial_value,increment", [(0, 1), (10, 5), (-5, 3), (100, -10)]
)
def test_redis_int_operations_sanity(initial_value, increment):
    # Arrange
    model = SimpleIntModel(count=initial_value)
    mock_redis = MagicMock()
    mock_redis.json().set = AsyncMock()
    mock_redis.json().numincrby = AsyncMock(return_value=initial_value + increment)
    model.count._base_model_link = model
    model.count.client = mock_redis

    # Act - Test assignment
    new_value = initial_value + increment
    model.count = new_value

    # Assert
    assert isinstance(model.count, RedisInt)
    assert int(model.count) == new_value
    assert model.count.key == model.key


@pytest.mark.parametrize("initial_value", [True, False])
def test_redis_bool_operations_sanity(initial_value):
    # Arrange
    model = SimpleBoolModel(flag=initial_value)
    mock_redis = MagicMock()
    mock_redis.json().set = AsyncMock()
    model.flag._base_model_link = model
    model.flag.client = mock_redis

    # Act - Test assignment
    new_value = not initial_value
    model.flag = new_value

    # Assert
    assert isinstance(model.flag, RedisBool)
    assert bool(model.flag) == new_value
    assert model.flag.key == model.key


@pytest.mark.parametrize(
    "initial_value,new_value",
    [(b"hello", b"world"), (b"", b"test"), (b"\x00\x01", b"\x02\x03")],
)
def test_redis_bytes_operations_sanity(initial_value, new_value):
    # Arrange
    model = SimpleBytesModel(data=initial_value)
    mock_redis = MagicMock()
    mock_redis.json().set = AsyncMock()
    model.data._base_model_link = model
    model.data.client = mock_redis

    # Act - Test assignment
    model.data = new_value

    # Assert
    assert isinstance(model.data, RedisBytes)
    assert bytes(model.data) == new_value
    assert model.data.key == model.key


def test_redis_str_concatenation_operation_sanity():
    # Arrange
    model = SimpleStringModel(name="hello")

    # Act
    result = model.name + " world"

    # Assert
    assert result == "hello world"
    assert isinstance(model.name, RedisStr)


def test_redis_int_arithmetic_operations_sanity():
    # Arrange
    model = SimpleIntModel(count=10)

    # Act & Assert
    assert model.count + 5 == 15
    assert model.count - 3 == 7
    assert model.count * 2 == 20
    assert model.count // 2 == 5
    assert isinstance(model.count, RedisInt)


def test_redis_bool_logical_operations_sanity():
    # Arrange
    model_true = SimpleBoolModel(flag=True)
    model_false = SimpleBoolModel(flag=False)

    # Act & Assert
    assert model_true.flag and True
    assert not (model_false.flag and True)
    assert model_true.flag or False
    assert not model_false.flag or True
    assert isinstance(model_true.flag, RedisBool)
    assert isinstance(model_false.flag, RedisBool)


def test_redis_bytes_operations_sanity():
    # Arrange
    model = SimpleBytesModel(data=b"hello")

    # Act & Assert
    assert model.data + b" world" == b"hello world"
    assert len(model.data) == 5
    assert isinstance(model.data, RedisBytes)
