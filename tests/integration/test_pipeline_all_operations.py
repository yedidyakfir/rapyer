import pytest
import pytest_asyncio

from redis_pydantic.base import BaseRedisModel


class ComprehensiveTestModel(BaseRedisModel):
    tags: list[str] = []
    metadata: dict[str, str] = {}
    name: str = ""
    counter: int = 0


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    ComprehensiveTestModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_pipeline_list_aappend__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["initial"])
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.tags.aappend("new_tag")
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.tags == ["initial"]

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.tags == ["initial", "new_tag"]


@pytest.mark.asyncio
async def test_pipeline_list_aextend__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["initial"])
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.tags.aextend(["tag1", "tag2"])
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.tags == ["initial"]

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.tags == ["initial", "tag1", "tag2"]


@pytest.mark.asyncio
async def test_pipeline_list_ainsert__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["first", "last"])
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.tags.ainsert(1, "middle")
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.tags == ["first", "last"]

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.tags == ["first", "middle", "last"]


@pytest.mark.asyncio
async def test_pipeline_list_aclear__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["tag1", "tag2"])
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.tags.aclear()
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.tags == ["tag1", "tag2"]

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.tags == []


@pytest.mark.asyncio
async def test_pipeline_dict_aset_item__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(metadata={"existing": "value"})
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.metadata.aset_item("new_key", "new_value")
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.metadata == {"existing": "value"}

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.metadata == {"existing": "value", "new_key": "new_value"}


@pytest.mark.asyncio
async def test_pipeline_dict_adel_item__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(metadata={"key1": "value1", "key2": "value2"})
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.metadata.adel_item("key1")
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.metadata == {"key1": "value1", "key2": "value2"}

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.metadata == {"key2": "value2"}


@pytest.mark.asyncio
async def test_pipeline_dict_aupdate__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(metadata={"existing": "value"})
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.metadata.aupdate(key1="value1", key2="value2")
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.metadata == {"existing": "value"}

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.metadata == {"existing": "value", "key1": "value1", "key2": "value2"}


@pytest.mark.asyncio
async def test_pipeline_dict_aclear__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(metadata={"key1": "value1", "key2": "value2"})
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.metadata.aclear()
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.metadata == {"key1": "value1", "key2": "value2"}

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.metadata == {}


@pytest.mark.asyncio
async def test_pipeline_string_set__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(name="original")
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.name.set("updated")
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.name == "original"

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.name == "updated"


@pytest.mark.asyncio
async def test_pipeline_int_set__check_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(counter=10)
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.counter.set(99)
        
        # Check if change is not applied yet (atomicity test)
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.counter == 10

    # Assert - Check if change was applied after pipeline
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.counter == 99


@pytest.mark.asyncio
async def test_pipeline_multiple_operations__check_combined_atomicity_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(
        tags=["tag1"], 
        metadata={"key1": "value1"}, 
        name="original", 
        counter=0
    )
    await model.save()

    # Act - Test multiple operations in single pipeline
    async with model.pipeline() as redis_model:
        await redis_model.tags.aappend("tag2")
        await redis_model.tags.aextend(["tag3", "tag4"])
        await redis_model.metadata.aupdate(key2="value2", key3="value3")
        await redis_model.metadata.aset_item("key4", "value4")
        await redis_model.name.set("updated")
        await redis_model.counter.set(100)
        
        # Check intermediate state - should be unchanged
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.tags == ["tag1"]
        assert loaded_model.metadata == {"key1": "value1"}
        assert loaded_model.name == "original"
        assert loaded_model.counter == 0

    # Assert - All changes should be applied atomically
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.tags == ["tag1", "tag2", "tag3", "tag4"]
    assert final_model.metadata == {"key1": "value1", "key2": "value2", "key3": "value3", "key4": "value4"}
    assert final_model.name == "updated"
    assert final_model.counter == 100


@pytest.mark.asyncio 
async def test_pipeline_exception_rollback__check_no_changes_applied_edge_case(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["original"], metadata={"key": "original"})
    await model.save()
    original_state = await ComprehensiveTestModel.get(model.key)

    # Act & Assert - Pipeline should rollback on exception
    with pytest.raises(ValueError, match="Test exception"):
        async with model.pipeline() as redis_model:
            await redis_model.tags.aappend("should_not_be_saved")
            await redis_model.metadata.aset_item("new_key", "should_not_be_saved")
            raise ValueError("Test exception")

    # Assert - No changes should be applied when exception occurs
    final_model = await ComprehensiveTestModel.get(model.key)
    assert final_model.tags == original_state.tags
    assert final_model.metadata == original_state.metadata


# Tests for operations that DON'T work in pipeline (kept with try-catch for documentation)
@pytest.mark.asyncio
async def test_pipeline_list_apop__check_pipeline_limitation_edge_case(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["tag1", "tag2", "tag3"])
    await model.save()

    # Act & Assert - apop doesn't work in pipeline context
    with pytest.raises(TypeError, match="Async Redis client does not support class retrieval"):
        async with model.pipeline() as redis_model:
            await redis_model.tags.apop()


@pytest.mark.asyncio
async def test_pipeline_dict_apop__check_pipeline_limitation_edge_case(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(metadata={"key1": "value1", "key2": "value2"})
    await model.save()

    # Act & Assert - dict apop doesn't work in pipeline context
    with pytest.raises(AttributeError, match="'Pipeline' object has no attribute 'startswith'"):
        async with model.pipeline() as redis_model:
            await redis_model.metadata.apop("key1")


@pytest.mark.asyncio
async def test_pipeline_dict_apopitem__check_pipeline_limitation_edge_case(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(metadata={"key1": "value1"})
    await model.save()

    # Act & Assert - apopitem doesn't work in pipeline context
    with pytest.raises(TypeError, match="Async Redis client does not support class retrieval"):
        async with model.pipeline() as redis_model:
            await redis_model.metadata.apopitem()