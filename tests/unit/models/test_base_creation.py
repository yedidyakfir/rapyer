from datetime import datetime

import pytest

from rapyer.types.dct import RedisDict
from tests.models.dict_models import (
    IntDictModel,
    StrDictModel,
    BytesDictModel,
    DatetimeDictModel,
    EnumDictModel,
    AnyDictModel,
    Status,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["model_class", "initial_data"],
    [
        [StrDictModel, {"key1": "value1"}],
        [IntDictModel, {"key1": 42}],
        [DatetimeDictModel, {"key1": datetime(2023, 1, 1)}],
        [BytesDictModel, {"key1": b"data1"}],
        [EnumDictModel, {"key1": Status.ACTIVE}],
        [AnyDictModel, {"key1": "mixed"}],
    ],
)
async def test_redis_dict__model_creation__check_redis_dict_instance_sanity(
    real_redis_client, model_class, initial_data
):
    # Arrange & Act
    user = model_class(metadata=initial_data)

    # Assert
    assert isinstance(user.metadata, RedisDict)
    assert hasattr(user.metadata, "key")
    assert hasattr(user.metadata, "field_path")
    assert hasattr(user.metadata, "redis")
    assert hasattr(user.metadata, "json_path")
    assert user.metadata.key == user.key
    assert user.metadata.field_path == "metadata"
    assert user.metadata.json_path == "$.metadata"
    assert user.metadata.redis == real_redis_client
