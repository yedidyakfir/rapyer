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


class MultiTypeModel(AtomicRedisModel):
    name: str
    count: int
    flag: bool
    data: bytes


@pytest.mark.parametrize("test_value", ["hello", "world", "", "test_string"])
def test_redis_str_model_creation_sanity(test_value):
    # Arrange & Act
    model = SimpleStringModel(name=test_value)

    # Assert
    assert isinstance(model.name, RedisStr)
    assert model.name.key == model.key
    assert model.name.field_path == "name"
    assert model.name.json_path == "$.name"
    assert str(model.name) == test_value


@pytest.mark.parametrize("test_value", [0, 1, -1, 100, -100])
def test_redis_int_model_creation_sanity(test_value):
    # Arrange & Act
    model = SimpleIntModel(count=test_value)

    # Assert
    assert isinstance(model.count, RedisInt)
    assert model.count.key == model.key
    assert model.count.field_path == "count"
    assert model.count.json_path == "$.count"
    assert int(model.count) == test_value


@pytest.mark.parametrize("test_value", [True, False])
def test_redis_bool_model_creation_sanity(test_value):
    # Arrange & Act
    model = SimpleBoolModel(flag=test_value)

    # Assert
    assert isinstance(model.flag, RedisBool)
    assert model.flag.key == model.key
    assert model.flag.field_path == "flag"
    assert model.flag.json_path == "$.flag"
    assert bool(model.flag) == test_value


@pytest.mark.parametrize("test_value", [b"hello", b"world", b"", b"\x00\x01\x02"])
def test_redis_bytes_model_creation_sanity(test_value):
    # Arrange & Act
    model = SimpleBytesModel(data=test_value)

    # Assert
    assert isinstance(model.data, RedisBytes)
    assert model.data.key == model.key
    assert model.data.field_path == "data"
    assert model.data.json_path == "$.data"
    assert bytes(model.data) == test_value


def test_multi_type_model_creation_sanity():
    # Arrange
    name_val = "test"
    count_val = 42
    flag_val = True
    data_val = b"binary"

    # Act
    model = MultiTypeModel(name=name_val, count=count_val, flag=flag_val, data=data_val)

    # Assert
    assert isinstance(model.name, RedisStr)
    assert isinstance(model.count, RedisInt)
    assert isinstance(model.flag, RedisBool)
    assert isinstance(model.data, RedisBytes)

    assert model.name.key == model.key
    assert model.count.key == model.key
    assert model.flag.key == model.key
    assert model.data.key == model.key

    assert model.name.field_path == "name"
    assert model.count.field_path == "count"
    assert model.flag.field_path == "flag"
    assert model.data.field_path == "data"

    assert model.name.json_path == "$.name"
    assert model.count.json_path == "$.count"
    assert model.flag.json_path == "$.flag"
    assert model.data.json_path == "$.data"


def test_empty_model_creation_sanity():
    # Arrange & Act
    model = MultiTypeModel()

    # Assert
    assert hasattr(model, "name")
    assert hasattr(model, "count")
    assert hasattr(model, "flag")
    assert hasattr(model, "data")
