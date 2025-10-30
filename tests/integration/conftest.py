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
    BaseDictMetadataModel,
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
    # All Redis models that need the client configured
    redis_models = [
        # Collection types - List models
        UserListModel,
        ProductListModel,
        IntListModel,
        StrListModel,
        DictListModel,
        BaseModelListModel,
        ListModel,
        # Collection types - Dict models
        BaseDictMetadataModel,
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
        # Collection types - Mixed and pipeline models
        MixedTypesModel,
        PipelineTestModel,
        ComprehensiveTestModel,
        # Simple types
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
        # Functionality types
        LockSaveTestModel,
        LockUpdateTestModel,
        RichModel,
        AllTypesModel,
        # Specialized types
        UserModel,
        # Complex types
        OuterModel,
        InnerRedisModel,
        OuterModelWithRedisNested,
        TestRedisModel,
    ]

    # Configure Redis client for all models
    for model in redis_models:
        model.Meta.redis = redis_client

    yield redis_client
    await redis_client.aclose()
