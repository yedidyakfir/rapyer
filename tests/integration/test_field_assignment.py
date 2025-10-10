import pytest
import pytest_asyncio
from pydantic import ValidationError

from redis_pydantic.types.boolean import RedisBool
from redis_pydantic.types.byte import RedisBytes
from redis_pydantic.types.dct import RedisDict
from redis_pydantic.types.integer import RedisInt
from redis_pydantic.types.lst import RedisList
from redis_pydantic.types.string import RedisStr
from tests.integration.test_base_redis_model import UserModel as BaseUserModel

# Import existing models from other test files
from tests.integration.test_base_redis_model_mixed_types import MixedTypesModel
from tests.integration.test_redis_bool import BoolModel
from tests.integration.test_redis_bytes import BytesModel
from tests.integration.test_redis_dict import UserModel as DictUserModel
from tests.integration.test_redis_int import IntModel
from tests.integration.test_redis_str import StrModel
from tests.integration.test_none_values import NoneTestModel


@pytest_asyncio.fixture
async def mixed_model(redis_client):
    MixedTypesModel.Meta.redis = redis_client
    yield MixedTypesModel()


@pytest_asyncio.fixture
async def user_model_with_tags(redis_client):
    BaseUserModel.Meta.redis = redis_client
    yield BaseUserModel(tags=["initial", "tags"])


@pytest_asyncio.fixture
async def str_model_with_values(redis_client):
    StrModel.Meta.redis = redis_client
    yield StrModel(name="initial_name", description="initial_desc")


@pytest_asyncio.fixture
async def int_model_with_values(redis_client):
    IntModel.Meta.redis = redis_client
    yield IntModel(count=50, score=200)


@pytest_asyncio.fixture
async def bool_model_with_values(redis_client):
    BoolModel.Meta.redis = redis_client
    yield BoolModel(is_active=True, is_deleted=False)


@pytest_asyncio.fixture
async def bytes_model_with_values(redis_client):
    BytesModel.Meta.redis = redis_client
    yield BytesModel(data=b"initial_data", binary_content=b"initial_binary")


@pytest_asyncio.fixture
async def dict_model_with_values(redis_client):
    DictUserModel.Meta.redis = redis_client
    yield DictUserModel(metadata={"key1": "value1", "key2": "value2"})


@pytest_asyncio.fixture
async def none_model_with_values(redis_client):
    NoneTestModel.Meta.redis = redis_client
    yield NoneTestModel(optional_string="test", optional_int=42)


# Constructor initialization tests
@pytest.mark.asyncio
async def test_constructor_string_fields_converted_to_redis_types_sanity(
    str_model_with_values,
):
    # Arrange & Act (done in fixture)

    # Assert - fields initialized in constructor should be Redis types
    assert isinstance(str_model_with_values.name, RedisStr)
    assert isinstance(str_model_with_values.description, RedisStr)

    # Assert - values preserved
    assert str(str_model_with_values.name) == "initial_name"
    assert str(str_model_with_values.description) == "initial_desc"


@pytest.mark.asyncio
async def test_constructor_list_field_converted_to_redis_type_sanity(
    user_model_with_tags,
):
    # Arrange & Act (done in fixture)

    # Assert - field initialized in constructor should be Redis type
    assert isinstance(user_model_with_tags.tags, RedisList)
    assert list(user_model_with_tags.tags) == ["initial", "tags"]


@pytest.mark.asyncio
async def test_constructor_int_fields_converted_to_redis_types_sanity(
    int_model_with_values,
):
    # Arrange & Act (done in fixture)

    # Assert - fields initialized in constructor should be Redis types
    assert isinstance(int_model_with_values.count, RedisInt)
    assert isinstance(int_model_with_values.score, RedisInt)

    # Assert - values preserved
    assert int(int_model_with_values.count) == 50
    assert int(int_model_with_values.score) == 200


@pytest.mark.asyncio
async def test_constructor_bool_fields_converted_to_redis_types_sanity(
    bool_model_with_values,
):
    # Arrange & Act (done in fixture)

    # Assert - fields initialized in constructor should be Redis types
    assert isinstance(bool_model_with_values.is_active, RedisBool)
    assert isinstance(bool_model_with_values.is_deleted, RedisBool)

    # Assert - values preserved
    assert bool(bool_model_with_values.is_active) is True
    assert bool(bool_model_with_values.is_deleted) is False


@pytest.mark.asyncio
async def test_constructor_bytes_fields_converted_to_redis_types_sanity(
    bytes_model_with_values,
):
    # Arrange & Act (done in fixture)

    # Assert - fields initialized in constructor should be Redis types
    assert isinstance(bytes_model_with_values.data, RedisBytes)
    assert isinstance(bytes_model_with_values.binary_content, RedisBytes)

    # Assert - values preserved
    assert bytes(bytes_model_with_values.data) == b"initial_data"
    assert bytes(bytes_model_with_values.binary_content) == b"initial_binary"


@pytest.mark.asyncio
async def test_constructor_dict_field_converted_to_redis_type_sanity(
    dict_model_with_values,
):
    # Arrange & Act (done in fixture)

    # Assert - field initialized in constructor should be Redis type
    assert isinstance(dict_model_with_values.metadata, RedisDict)
    assert dict(dict_model_with_values.metadata) == {"key1": "value1", "key2": "value2"}


# Post-construction assignment tests
@pytest.mark.asyncio
async def test_assignment_string_field_converts_to_redis_type_sanity(
    str_model_with_values,
):
    # Arrange & Act
    str_model_with_values.name = "updated_name"
    str_model_with_values.description = "updated_description"

    # Assert
    assert isinstance(str_model_with_values.name, RedisStr)
    assert isinstance(str_model_with_values.description, RedisStr)
    assert str(str_model_with_values.name) == "updated_name"
    assert str(str_model_with_values.description) == "updated_description"


@pytest.mark.asyncio
async def test_assignment_list_field_converts_to_redis_type_sanity(
    user_model_with_tags,
):
    # Arrange & Act
    user_model_with_tags.tags = ["python", "redis", "testing"]

    # Assert
    assert isinstance(user_model_with_tags.tags, RedisList)
    assert list(user_model_with_tags.tags) == ["python", "redis", "testing"]


@pytest.mark.asyncio
async def test_assignment_int_fields_convert_to_redis_types_sanity(
    int_model_with_values,
):
    # Arrange & Act
    int_model_with_values.count = 100
    int_model_with_values.score = 500

    # Assert
    assert isinstance(int_model_with_values.count, RedisInt)
    assert isinstance(int_model_with_values.score, RedisInt)
    assert int(int_model_with_values.count) == 100
    assert int(int_model_with_values.score) == 500


@pytest.mark.asyncio
async def test_assignment_bool_fields_convert_to_redis_types_sanity(
    bool_model_with_values,
):
    # Arrange & Act
    bool_model_with_values.is_active = False
    bool_model_with_values.is_deleted = True

    # Assert
    assert isinstance(bool_model_with_values.is_active, RedisBool)
    assert isinstance(bool_model_with_values.is_deleted, RedisBool)
    assert bool(bool_model_with_values.is_active) is False
    assert bool(bool_model_with_values.is_deleted) is True


@pytest.mark.asyncio
async def test_assignment_bytes_fields_convert_to_redis_types_sanity(
    bytes_model_with_values,
):
    # Arrange & Act
    bytes_model_with_values.data = b"updated_data"
    bytes_model_with_values.binary_content = b"updated_binary"

    # Assert
    assert isinstance(bytes_model_with_values.data, RedisBytes)
    assert isinstance(bytes_model_with_values.binary_content, RedisBytes)
    assert bytes(bytes_model_with_values.data) == b"updated_data"
    assert bytes(bytes_model_with_values.binary_content) == b"updated_binary"


@pytest.mark.asyncio
async def test_assignment_dict_field_converts_to_redis_type_sanity(
    dict_model_with_values,
):
    # Arrange & Act
    dict_model_with_values.metadata = {"new_key": "new_value", "another": "pair"}

    # Assert
    assert isinstance(dict_model_with_values.metadata, RedisDict)
    assert dict(dict_model_with_values.metadata) == {
        "new_key": "new_value",
        "another": "pair",
    }


@pytest.mark.asyncio
async def test_assignment_mixed_types_all_convert_sanity(mixed_model):
    # Arrange & Act
    mixed_model.str_list = ["string1", "string2"]
    mixed_model.int_list = [1, 2, 3]
    mixed_model.bool_list = [True, False, True]
    mixed_model.bytes_list = [b"bytes1", b"bytes2"]
    mixed_model.str_dict = {"key": "value"}
    mixed_model.int_dict = {"count": 42}
    mixed_model.bool_dict = {"active": True}
    mixed_model.bytes_dict = {"data": b"binary"}

    # Assert - types
    assert isinstance(mixed_model.str_list, RedisList)
    assert isinstance(mixed_model.int_list, RedisList)
    assert isinstance(mixed_model.bool_list, RedisList)
    assert isinstance(mixed_model.bytes_list, RedisList)
    assert isinstance(mixed_model.str_dict, RedisDict)
    assert isinstance(mixed_model.int_dict, RedisDict)
    assert isinstance(mixed_model.bool_dict, RedisDict)
    assert isinstance(mixed_model.bytes_dict, RedisDict)

    # Assert - values
    assert list(mixed_model.str_list) == ["string1", "string2"]
    assert list(mixed_model.int_list) == [1, 2, 3]
    assert list(mixed_model.bool_list) == [True, False, True]
    assert list(mixed_model.bytes_list) == [b"bytes1", b"bytes2"]
    assert dict(mixed_model.str_dict) == {"key": "value"}
    assert dict(mixed_model.int_dict) == {"count": 42}
    assert dict(mixed_model.bool_dict) == {"active": True}
    assert dict(mixed_model.bytes_dict) == {"data": b"binary"}


# Edge cases
@pytest.mark.asyncio
async def test_reassignment_overwrites_correctly_sanity(user_model_with_tags):
    # Arrange
    initial_tags = list(user_model_with_tags.tags)

    # Act
    user_model_with_tags.tags = ["new", "tags", "list"]

    # Assert
    assert isinstance(user_model_with_tags.tags, RedisList)
    assert list(user_model_with_tags.tags) == ["new", "tags", "list"]
    assert list(user_model_with_tags.tags) != initial_tags


@pytest.mark.asyncio
async def test_numeric_type_coercion_edge_case(int_model_with_values):
    # Arrange & Act
    int_model_with_values.count = 42.0  # float should convert to int

    # Assert
    assert isinstance(int_model_with_values.count, RedisInt)
    assert int(int_model_with_values.count) == 42


@pytest.mark.asyncio
async def test_empty_collections_assignment_edge_case(mixed_model):
    # Arrange & Act
    mixed_model.str_list = []
    mixed_model.str_dict = {}

    # Assert
    assert isinstance(mixed_model.str_list, RedisList)
    assert isinstance(mixed_model.str_dict, RedisDict)
    assert list(mixed_model.str_list) == []
    assert dict(mixed_model.str_dict) == {}


@pytest.mark.asyncio
async def test_assignment_preserves_previous_field_conversions_sanity(
    str_model_with_values,
):
    # Arrange
    str_model_with_values.name = "first_update"

    # Act
    str_model_with_values.description = "second_update"

    # Assert - both fields should still be Redis types
    assert isinstance(str_model_with_values.name, RedisStr)
    assert isinstance(str_model_with_values.description, RedisStr)
    assert str(str_model_with_values.name) == "first_update"
    assert str(str_model_with_values.description) == "second_update"


@pytest.mark.asyncio
async def test_assignment_none_to_nullable_field_sanity(none_model_with_values):
    # Arrange & Act
    none_model_with_values.optional_string = None
    none_model_with_values.optional_int = None

    # Assert
    assert none_model_with_values.optional_string is None
    assert none_model_with_values.optional_int is None


@pytest.mark.asyncio
async def test_assignment_none_to_non_nullable_field_validation_error():
    # Arrange & Act
    with pytest.raises(ValidationError):
        StrModel(name=None)
