import pytest
import pytest_asyncio
from typing import List
from pydantic import Field

from rapyer.base import AtomicRedisModel


class LockTestModel(AtomicRedisModel):
    name: str = ""
    age: int = 0
    tags: List[str] = Field(default_factory=list)
    active: bool = True


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    LockTestModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_lock_model_changes_not_saved_with_save_at_end_false_sanity(
    real_redis_client,
):
    # Arrange
    original_model = LockTestModel(name="original", age=25, tags=["tag1"], active=True)
    await original_model.save()

    # Act
    async with LockTestModel.lock_from_key(
        original_model.key, save_at_end=False
    ) as locked_model:
        locked_model.name = "modified"
        locked_model.age = 30
        locked_model.tags.append("tag2")
        locked_model.active = False

    # Assert
    retrieved_model = await LockTestModel.get(original_model.key)
    assert retrieved_model.name == "original"
    assert retrieved_model.age == 25
    assert retrieved_model.tags == ["tag1"]
    assert retrieved_model.active == True


@pytest.mark.asyncio
async def test_lock_redis_operations_still_work_with_save_at_end_false_sanity(
    real_redis_client,
):
    # Arrange
    original_model = LockTestModel(name="original", age=25, tags=["tag1"], active=True)
    await original_model.save()

    # Act
    async with LockTestModel.lock_from_key(
        original_model.key, save_at_end=False
    ) as locked_model:
        await locked_model.tags.aappend("tag2")
        await locked_model.tags.aappend("tag3")

    # Assert
    retrieved_model = await LockTestModel.get(original_model.key)
    assert "tag2" in retrieved_model.tags
    assert "tag3" in retrieved_model.tags


@pytest.mark.asyncio
async def test_lock_model_deletion_persists_with_save_at_end_false_sanity(
    real_redis_client,
):
    # Arrange
    model = LockTestModel(name="to_delete", age=25)
    await model.save()
    model_key = model.key

    # Verify model exists
    retrieved_model = await LockTestModel.get(model_key)
    assert retrieved_model.name == "to_delete"

    # Act
    async with LockTestModel.lock_from_key(
        model_key, save_at_end=False
    ) as locked_model:
        await locked_model.delete()

    # Assert
    with pytest.raises(Exception):
        await LockTestModel.get(model_key)


@pytest.mark.asyncio
async def test_lock_model_field_modifications_vs_redis_operations_with_save_at_end_false_edge_case(
    real_redis_client,
):
    # Arrange
    model = LockTestModel(name="test", age=20, tags=["initial"])
    await model.save()

    # Act
    async with LockTestModel.lock_from_key(
        model.key, save_at_end=False
    ) as locked_model:
        # Field modification (should not persist)
        locked_model.name = "field_modified"
        locked_model.age = 99

        # Redis operation (should persist)
        await locked_model.tags.aappend("redis_added")

    # Assert
    retrieved_model = await LockTestModel.get(model.key)
    assert retrieved_model.name == "test"
    assert retrieved_model.age == 20
    assert "redis_added" in retrieved_model.tags
