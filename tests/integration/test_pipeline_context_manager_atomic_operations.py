import pytest
import pytest_asyncio

from redis_pydantic.base import BaseRedisModel


class PipelineTestModel(BaseRedisModel):
    metadata: dict[str, str] = {}
    config: dict[str, int] = {}


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    PipelineTestModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_pipeline_context_manager__dict_update_operations__check_atomic_batch_sanity(
    real_redis_client,
):
    # Arrange
    original_metadata = {"original": "value"}
    model = PipelineTestModel(metadata=original_metadata)
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.metadata.aupdate(key1="value1", key2="value2")
        await redis_model.metadata.aupdate(key3="value3", key4="value4")

        # Check that none of the operations have been applied to Redis yet
        loaded_model = await PipelineTestModel.get(model.key)
        assert loaded_model.metadata == original_metadata

    # Assert - All dict operations should be applied atomically
    final_model = await PipelineTestModel.get(model.key)
    expected_metadata = {
        "original": "value",
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "key4": "value4",
    }
    assert final_model.metadata == expected_metadata


@pytest.mark.asyncio
async def test_pipeline_context_manager__multiple_dict_fields__check_atomic_execution_sanity(
    real_redis_client,
):
    # Arrange
    model = PipelineTestModel(metadata={"env": "dev"}, config={"port": 8080})
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        await redis_model.metadata.aupdate(status="active", version="1.0")
        await redis_model.config.aupdate(timeout=30, retries=3)

        # Check that none of the operations have been applied to Redis yet
        loaded_model_1 = await PipelineTestModel.get(model.key)
        assert loaded_model_1.metadata == {"env": "dev"}

        await redis_model.metadata.aupdate(region="us-east")

        # Check again that changes still haven't been applied
        loaded_model_2 = await PipelineTestModel.get(model.key)
        assert loaded_model_2.metadata == {"env": "dev"}
        assert loaded_model_2.config == {"port": 8080}

    # Assert - All changes should be applied atomically
    final_model = await PipelineTestModel.get(model.key)
    assert final_model.metadata == {
        "env": "dev",
        "status": "active",
        "version": "1.0",
        "region": "us-east",
    }
    assert final_model.config == {"port": 8080, "timeout": 30, "retries": 3}


@pytest.mark.asyncio
async def test_pipeline_context_manager__exception_during_pipeline__check_no_changes_applied_edge_case(
    real_redis_client,
):
    # Arrange
    model = PipelineTestModel(metadata={"key": "original"})
    await model.save()
    original_data = await PipelineTestModel.get(model.key)

    # Act & Assert
    with pytest.raises(ValueError, match="Test exception"):
        async with model.pipeline() as redis_model:
            await redis_model.metadata.aupdate(should_not_be_saved="value")
            raise ValueError("Test exception")

    # Assert - No changes should be applied when exception occurs
    final_model = await PipelineTestModel.get(model.key)
    assert final_model.metadata == original_data.metadata


@pytest.mark.asyncio
async def test_pipeline_context_manager__empty_pipeline__check_no_operations_edge_case(
    real_redis_client,
):
    # Arrange
    model = PipelineTestModel(metadata={"key": "unchanged"})
    await model.save()
    original_data = await PipelineTestModel.get(model.key)

    # Act
    async with model.pipeline() as redis_model:
        pass  # No operations

    # Assert - Data should remain unchanged
    final_model = await PipelineTestModel.get(model.key)
    assert final_model.metadata == original_data.metadata


@pytest.mark.asyncio
async def test_pipeline_context_manager__incremental_updates_atomic__check_intermediate_state_sanity(
    real_redis_client,
):
    # Arrange
    model = PipelineTestModel(metadata={"stage": "init"}, config={"step": 0})
    await model.save()

    # Act
    async with model.pipeline() as redis_model:
        # First update
        await redis_model.metadata.aupdate(stage="processing", started_at="2023-01-01")

        # Check Redis state - should still be original
        loaded_model_1 = await PipelineTestModel.get(model.key)
        assert loaded_model_1.metadata == {"stage": "init"}
        assert loaded_model_1.config == {"step": 0}

        # Second update
        await redis_model.config.aupdate(step=1, timeout=30)

        # Check Redis state again - should still be original
        loaded_model_2 = await PipelineTestModel.get(model.key)
        assert loaded_model_2.metadata == {"stage": "init"}
        assert loaded_model_2.config == {"step": 0}

        # Third update
        await redis_model.metadata.aupdate(stage="completed")

    # Assert - All updates should be applied atomically
    final_model = await PipelineTestModel.get(model.key)
    assert final_model.metadata == {"stage": "completed", "started_at": "2023-01-01"}
    assert final_model.config == {"step": 1, "timeout": 30}


@pytest.mark.asyncio
async def test_pipeline_context_manager__pipeline_context_cleanup__check_context_variable_sanity(
    real_redis_client,
):
    # Arrange
    model = PipelineTestModel(metadata={"test": "value"})
    await model.save()

    from redis_pydantic.context import _context_var

    # Act & Assert - Context should be None before pipeline
    assert _context_var.get() is None

    async with model.pipeline() as redis_model:
        # Context should be set to pipeline inside context
        assert _context_var.get() is not None
        await redis_model.metadata.aupdate(updated="true")

    # Context should be cleared after pipeline
    assert _context_var.get() is None

    # Verify operation was executed
    final_model = await PipelineTestModel.get(model.key)
    assert final_model.metadata == {"test": "value", "updated": "true"}
