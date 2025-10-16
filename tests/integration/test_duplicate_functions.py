import pytest
import pytest_asyncio
from pydantic import Field, BaseModel

from rapyer.base import AtomicRedisModel
from tests.integration.test_nested_redis_models import (
    InnerRedisModel,
    ContainerModel,
    OuterModelWithRedisNested,
)


class InnerMostModel(BaseModel):
    names: list[str] = Field(default_factory=list)
    scores: dict[str, int] = Field(default_factory=dict)
    counter: int = 0


class MiddleModel(BaseModel):
    inner_model: InnerMostModel = Field(default_factory=InnerMostModel)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class TestRedisModel(AtomicRedisModel):
    middle_model: MiddleModel = Field(default_factory=MiddleModel)
    user_data: dict[str, int] = Field(default_factory=dict)
    items: list[int] = Field(default_factory=list)
    description: str = "test_model"


@pytest_asyncio.fixture
async def redis_client_fixture(redis_client):
    TestRedisModel.Meta.redis = redis_client
    InnerRedisModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_duplicate_basic_functionality_sanity(redis_client_fixture):
    # Arrange
    original = TestRedisModel(
        description="original", items=[1, 2, 3], user_data={"user1": 100, "user2": 200}
    )
    await original.save()

    # Act
    duplicate = await original.duplicate()

    # Assert
    assert duplicate.pk != original.pk
    assert duplicate.description == original.description
    assert duplicate.items == original.items
    assert duplicate.user_data == original.user_data

    # Verify both exist in Redis
    original_exists = await redis_client_fixture.exists(original.key)
    duplicate_exists = await redis_client_fixture.exists(duplicate.key)
    assert original_exists == 1
    assert duplicate_exists == 1


@pytest.mark.asyncio
async def test_duplicate_with_nested_models_sanity(redis_client_fixture):
    # Arrange
    inner_model = InnerMostModel(
        names=["alice", "bob"], scores={"alice": 95, "bob": 87}, counter=42
    )
    middle_model = MiddleModel(
        inner_model=inner_model,
        tags=["important", "test"],
        metadata={"env": "staging", "version": "1.0"},
    )
    original = TestRedisModel(
        middle_model=middle_model,
        user_data={"admin": 1000},
        items=[10, 20, 30],
        description="complex_model",
    )
    await original.save()

    # Act
    duplicate = await original.duplicate()

    # Assert
    assert duplicate.pk != original.pk
    assert (
        duplicate.middle_model.inner_model.names
        == original.middle_model.inner_model.names
    )
    assert (
        duplicate.middle_model.inner_model.scores
        == original.middle_model.inner_model.scores
    )
    assert (
        duplicate.middle_model.inner_model.counter
        == original.middle_model.inner_model.counter
    )
    assert duplicate.middle_model.tags == original.middle_model.tags
    assert duplicate.middle_model.metadata == original.middle_model.metadata
    assert duplicate.user_data == original.user_data
    assert duplicate.items == original.items
    assert duplicate.description == original.description


@pytest.mark.asyncio
async def test_duplicate_many_functionality_sanity(redis_client_fixture):
    # Arrange
    original = TestRedisModel(
        description="original_for_many", items=[5, 10, 15], user_data={"batch": 999}
    )
    await original.save()

    # Act
    duplicates = await original.duplicate_many(3)

    # Assert
    assert len(duplicates) == 3

    # Check all have different keys
    pks = [duplicate.pk for duplicate in duplicates]
    assert len(set(pks)) == 3  # All unique
    assert original.pk not in pks  # Original not in duplicates

    # Check all have same values
    for duplicate in duplicates:
        assert duplicate.description == original.description
        assert duplicate.items == original.items
        assert duplicate.user_data == original.user_data

    # Verify all exist in Redis
    for duplicate in duplicates:
        exists = await redis_client_fixture.exists(duplicate.key)
        assert exists == 1


@pytest.mark.asyncio
async def test_duplicate_redis_operations_on_duplicated_models_sanity(
    redis_client_fixture,
):
    # Arrange
    original = TestRedisModel(items=[1, 2], user_data={"count": 10})
    await original.save()

    # Act
    duplicate = await original.duplicate()

    # Perform Redis operations on duplicate
    await duplicate.items.aappend(3)
    await duplicate.user_data.aset_item("new_key", 20)

    # Assert
    # Original should remain unchanged
    await original.items.load()
    await original.user_data.load()
    assert original.items == [1, 2]
    assert original.user_data == {"count": 10}

    # Duplicate should have changes
    assert duplicate.items == [1, 2, 3]
    assert duplicate.user_data == {"count": 10, "new_key": 20}


@pytest.mark.asyncio
async def test_duplicate_redis_operations_on_nested_models_sanity(redis_client_fixture):
    # Arrange
    original = TestRedisModel()
    await original.save()

    # Act
    duplicate = await original.duplicate()

    # Perform Redis operations on nested models in duplicate
    await duplicate.middle_model.tags.aappend("nested_tag")
    await duplicate.middle_model.metadata.aset_item("nested_key", "nested_value")
    await duplicate.middle_model.inner_model.names.aappend("nested_name")

    # Assert
    # Original should remain unchanged
    await original.middle_model.tags.load()
    await original.middle_model.metadata.load()
    await original.middle_model.inner_model.names.load()
    assert original.middle_model.tags == []
    assert original.middle_model.metadata == {}
    assert original.middle_model.inner_model.names == []

    # Duplicate should have changes
    assert duplicate.middle_model.tags == ["nested_tag"]
    assert duplicate.middle_model.metadata == {"nested_key": "nested_value"}
    assert duplicate.middle_model.inner_model.names == ["nested_name"]


@pytest.mark.asyncio
async def test_duplicate_with_redis_nested_models_sanity(redis_client_fixture):
    # Arrange
    inner_redis = InnerRedisModel(
        tags=["redis_tag"], metadata={"redis_key": "redis_value"}, counter=5
    )
    container = ContainerModel(inner_redis=inner_redis, description="redis_container")
    original = OuterModelWithRedisNested(container=container, outer_data=[100, 200])
    await original.save()

    # Act
    duplicate = await original.duplicate()

    # Assert
    assert duplicate.pk != original.pk
    assert duplicate.container.inner_redis.tags == original.container.inner_redis.tags
    assert (
        duplicate.container.inner_redis.metadata
        == original.container.inner_redis.metadata
    )
    assert (
        duplicate.container.inner_redis.counter
        == original.container.inner_redis.counter
    )
    assert duplicate.container.description == original.container.description
    assert duplicate.outer_data == original.outer_data


@pytest.mark.asyncio
async def test_duplicate_redis_operations_on_redis_nested_models_sanity(
    redis_client_fixture,
):
    # Arrange
    original = OuterModelWithRedisNested()
    await original.save()

    # Act
    duplicate = await original.duplicate()

    # Perform Redis operations on nested Redis models in duplicate
    await duplicate.container.inner_redis.tags.aappend("redis_nested_tag")
    await duplicate.container.inner_redis.metadata.aset_item(
        "redis_nested_key", "redis_nested_value"
    )
    await duplicate.outer_data.aappend(300)

    # Assert
    # Original should remain unchanged
    await original.container.inner_redis.tags.load()
    await original.container.inner_redis.metadata.load()
    await original.outer_data.load()
    assert original.container.inner_redis.tags == []
    assert original.container.inner_redis.metadata == {}
    assert original.outer_data == []

    # Duplicate should have changes
    assert duplicate.container.inner_redis.tags == ["redis_nested_tag"]
    assert duplicate.container.inner_redis.metadata == {
        "redis_nested_key": "redis_nested_value"
    }
    assert duplicate.outer_data == [300]


@pytest.mark.asyncio
async def test_cannot_duplicate_inner_model_edge_case(redis_client_fixture):
    # Arrange
    original = TestRedisModel()
    await original.save()

    # Act & Assert
    # Try to duplicate inner model - should fail
    with pytest.raises(RuntimeError, match="Can only duplicate from top level model"):
        await original.middle_model.duplicate()

    with pytest.raises(RuntimeError, match="Can only duplicate from top level model"):
        await original.middle_model.duplicate_many(2)


@pytest.mark.asyncio
async def test_cannot_duplicate_redis_inner_model_edge_case(redis_client_fixture):
    # Arrange
    original = OuterModelWithRedisNested()
    await original.save()

    # Act & Assert
    # Try to duplicate Redis inner model - should fail
    with pytest.raises(RuntimeError, match="Can only duplicate from top level model"):
        await original.container.inner_redis.duplicate()

    with pytest.raises(RuntimeError, match="Can only duplicate from top level model"):
        await original.container.inner_redis.duplicate_many(2)


@pytest.mark.parametrize("num_duplicates", [1, 3, 5])
@pytest.mark.asyncio
async def test_duplicate_many_with_different_counts_sanity(
    redis_client_fixture, num_duplicates
):
    # Arrange
    original = TestRedisModel(description=f"original_for_{num_duplicates}")
    await original.save()

    # Act
    duplicates = await original.duplicate_many(num_duplicates)

    # Assert
    assert len(duplicates) == num_duplicates

    # Check all have different keys
    pks = [duplicate.pk for duplicate in duplicates]
    assert len(set(pks)) == num_duplicates
    assert original.pk not in pks

    # Verify all exist in Redis
    for duplicate in duplicates:
        exists = await redis_client_fixture.exists(duplicate.key)
        assert exists == 1
        assert duplicate.description == original.description


@pytest.mark.asyncio
async def test_duplicate_preserves_all_redis_types_sanity(redis_client_fixture):
    # Arrange
    inner_model = InnerMostModel(
        names=["test1", "test2"], scores={"test1": 100, "test2": 90}, counter=15
    )
    middle_model = MiddleModel(
        inner_model=inner_model,
        tags=["tag1", "tag2"],
        metadata={"key1": "value1", "key2": "value2"},
    )
    original = TestRedisModel(
        middle_model=middle_model,
        user_data={"user1": 50, "user2": 75},
        items=[10, 20, 30, 40],
        description="comprehensive_test",
    )
    await original.save()

    # Act
    duplicate = await original.duplicate()

    # Assert
    assert duplicate.pk != original.pk

    # Check all list types
    assert (
        duplicate.middle_model.inner_model.names
        == original.middle_model.inner_model.names
    )
    assert duplicate.middle_model.tags == original.middle_model.tags
    assert duplicate.items == original.items

    # Check all dict types
    assert (
        duplicate.middle_model.inner_model.scores
        == original.middle_model.inner_model.scores
    )
    assert duplicate.middle_model.metadata == original.middle_model.metadata
    assert duplicate.user_data == original.user_data

    # Check scalar types
    assert (
        duplicate.middle_model.inner_model.counter
        == original.middle_model.inner_model.counter
    )
    assert duplicate.description == original.description
