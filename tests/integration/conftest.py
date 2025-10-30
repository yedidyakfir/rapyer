import pytest_asyncio

import rapyer

# Collection types
from tests.models.collection_types import (
    UserListModel,
    ProductListModel,
    IntListModel,
    StrListModel,
    DictListModel,
    BaseModelListModel,
    ListModel,
    IntDictModel,
    StrDictModel,
    DictDictModel,
    BaseModelDictSetitemModel,
    BytesDictModel,
    DatetimeDictModel,
    EnumDictModel,
    AnyDictModel,
    BaseModelDictModel,
    BoolDictModel,
    ListDictModel,
    NestedDictModel,
    DictModel,
    MixedTypesModel,
    PipelineTestModel,
    ComprehensiveTestModel,
)

# Complex types
from tests.models.complex_types import (
    OuterModel,
    InnerRedisModel,
    OuterModelWithRedisNested,
    TestRedisModel,
)

# Functionality types
from tests.models.functionality_types import (
    LockSaveTestModel,
    LockUpdateTestModel,
    RichModel,
    AllTypesModel,
)

# Simple types
from tests.models.simple_types import (
    IntModel,
    BoolModel,
    StrModel,
    BytesModel,
    DatetimeModel,
    DatetimeListModel,
    DatetimeDictModel,
    UserModelWithTTL,
    UserModelWithoutTTL,
    TaskModel,
    NoneTestModel,
)

# Specialized types
from tests.models.specialized import UserModel


@pytest_asyncio.fixture
async def redis_client():
    meta_redis = rapyer.AtomicRedisModel.Meta.redis
    redis = meta_redis.from_url("redis://localhost:6370/0", decode_responses=True)
    await redis.flushdb()
    yield redis
    await redis.flushdb()


@pytest_asyncio.fixture(autouse=True)
async def real_redis_client(redis_client):
    # Collection types - List models
    UserListModel.Meta.redis = redis_client
    ProductListModel.Meta.redis = redis_client
    IntListModel.Meta.redis = redis_client
    StrListModel.Meta.redis = redis_client
    DictListModel.Meta.redis = redis_client
    BaseModelListModel.Meta.redis = redis_client
    ListModel.Meta.redis = redis_client

    # Collection types - Dict models
    IntDictModel.Meta.redis = redis_client
    StrDictModel.Meta.redis = redis_client
    DictDictModel.Meta.redis = redis_client
    BaseModelDictSetitemModel.Meta.redis = redis_client
    BytesDictModel.Meta.redis = redis_client
    DatetimeDictModel.Meta.redis = redis_client
    EnumDictModel.Meta.redis = redis_client
    AnyDictModel.Meta.redis = redis_client
    BaseModelDictModel.Meta.redis = redis_client
    BoolDictModel.Meta.redis = redis_client
    ListDictModel.Meta.redis = redis_client
    NestedDictModel.Meta.redis = redis_client
    DictModel.Meta.redis = redis_client

    # Collection types - Mixed and pipeline models
    MixedTypesModel.Meta.redis = redis_client
    PipelineTestModel.Meta.redis = redis_client
    ComprehensiveTestModel.Meta.redis = redis_client

    # Simple types
    IntModel.Meta.redis = redis_client
    BoolModel.Meta.redis = redis_client
    StrModel.Meta.redis = redis_client
    BytesModel.Meta.redis = redis_client
    DatetimeModel.Meta.redis = redis_client
    DatetimeListModel.Meta.redis = redis_client
    DatetimeDictModel.Meta.redis = redis_client
    UserModelWithTTL.Meta.redis = redis_client
    UserModelWithoutTTL.Meta.redis = redis_client
    TaskModel.Meta.redis = redis_client
    NoneTestModel.Meta.redis = redis_client

    # Functionality types
    LockSaveTestModel.Meta.redis = redis_client
    LockUpdateTestModel.Meta.redis = redis_client
    RichModel.Meta.redis = redis_client
    AllTypesModel.Meta.redis = redis_client

    # Specialized types
    UserModel.Meta.redis = redis_client

    # Complex types
    OuterModel.Meta.redis = redis_client
    InnerRedisModel.Meta.redis = redis_client
    OuterModelWithRedisNested.Meta.redis = redis_client
    TestRedisModel.Meta.redis = redis_client

    yield redis_client
    await redis_client.aclose()
