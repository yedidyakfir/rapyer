import pytest

import rapyer
from tests.models.simple_types import (
    StrModel,
    IntModel,
    BoolModel,
    BytesModel,
    DatetimeModel,
)
from tests.models.collection_types import ListModel, DictModel, ComprehensiveTestModel
from tests.models.complex_types import OuterModel, TestRedisModel
from tests.models.redis_types import DirectRedisStringModel, MixedDirectRedisTypesModel


@pytest.mark.parametrize(
    ["model_instance"],
    [
        [StrModel(name="test_user", description="test description")],
        [IntModel(count=42, score=100)],
        [BoolModel(is_active=True, is_deleted=False)],
        [BytesModel(data=b"test_data", binary_content=b"binary_test")],
        [DatetimeModel()],
        [ListModel(items=["item1", "item2"], numbers=[1, 2, 3])],
        [DictModel(data={"key1": "value1"}, config={"setting1": 10})],
        [
            ComprehensiveTestModel(
                tags=["tag1", "tag2"],
                metadata={"key": "value"},
                name="comprehensive",
                counter=5,
            )
        ],
        [OuterModel(user_data={"user": 123}, items=[10, 20])],
        [
            TestRedisModel(
                user_data={"test": 456}, items=[30, 40], description="test_redis"
            )
        ],
        [DirectRedisStringModel(name="redis_string_test")],
        [
            MixedDirectRedisTypesModel(
                name="mixed_test",
                count=99,
                active=True,
                tags=["redis1", "redis2"],
                config={"config_key": 100},
            )
        ],
    ],
)
@pytest.mark.asyncio
async def test_rapyer_get_functionality_sanity(model_instance):
    # Arrange
    await model_instance.save()
    redis_key = model_instance.key

    # Act
    retrieved_model = await rapyer.get(redis_key)

    # Assert
    assert retrieved_model == model_instance
