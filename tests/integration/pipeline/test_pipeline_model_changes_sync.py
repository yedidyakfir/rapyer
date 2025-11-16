import pytest

from tests.models.functionality_types import AllTypesModel


class TestPipelineStringField:
    @pytest.mark.asyncio
    async def test_assignment_changes_not_persisted_without_save_edge_case(self):
        # Arrange
        model = AllTypesModel(str_field="initial")
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.str_field = "new_value"

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.str_field == "initial"

        # Assert - direct assignment without save() is not committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        # Assignment without save() doesn't persist
        assert final_model.str_field == "initial"

    @pytest.mark.asyncio
    async def test_concatenation_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel(str_field="base")
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.str_field += "_suffix"

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.str_field == "base"

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.str_field == "base_suffix"

    @pytest.mark.asyncio
    async def test_multiple_updates_changes_preserved_during_pipeline_committed_after_edge_case(
        self,
    ):
        # Arrange
        model = AllTypesModel(str_field="start")
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.str_field += "_first"
            redis_model.str_field += "_second"

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.str_field == "start"

        # Assert - all accumulated changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.str_field == "start_first_second"


class TestPipelineIntegerField:
    @pytest.mark.asyncio
    async def test_assignment_changes_not_persisted_without_save_edge_case(self):
        # Arrange
        model = AllTypesModel(int_field=10)
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.int_field = 50

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.int_field == 10

        # Assert - direct assignment without save() is not committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.int_field == 10  # Assignment without save() doesn't persist

    @pytest.mark.asyncio
    async def test_addition_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel(int_field=100)
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.int_field += 25

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.int_field == 100

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.int_field == 125

    @pytest.mark.asyncio
    async def test_multiple_operations_changes_preserved_during_pipeline_committed_after_edge_case(
        self,
    ):
        # Arrange
        model = AllTypesModel(int_field=50)
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.int_field += 10
            redis_model.int_field += 20

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.int_field == 50

        # Assert - all accumulated changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.int_field == 80


class TestPipelineListField:
    @pytest.mark.asyncio
    async def test_append_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.list_field.append("item1")

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.list_field == []

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.list_field == ["item1"]

    @pytest.mark.asyncio
    async def test_aappend_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            await redis_model.list_field.aappend("async_item")

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.list_field == []

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.list_field == ["async_item"]

    @pytest.mark.asyncio
    async def test_extend_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.list_field.extend(["item1", "item2"])

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.list_field == []

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.list_field == ["item1", "item2"]

    @pytest.mark.asyncio
    async def test_aextend_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            await redis_model.list_field.aextend(["async_item1", "async_item2"])

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.list_field == []

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.list_field == ["async_item1", "async_item2"]

    @pytest.mark.asyncio
    async def test_mixed_operations_changes_preserved_during_pipeline_committed_after_edge_case(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.list_field.append("sync_item")
            await redis_model.list_field.aappend("async_item")
            redis_model.list_field.extend(["extend1", "extend2"])

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.list_field == []

        # Assert - all changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert "sync_item" in final_model.list_field
        assert "async_item" in final_model.list_field
        assert "extend1" in final_model.list_field
        assert "extend2" in final_model.list_field


class TestPipelineDictField:
    @pytest.mark.asyncio
    async def test_update_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.dict_field.update({"key1": "value1", "key2": "value2"})

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.dict_field == {}

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.dict_field == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_aupdate_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            await redis_model.dict_field.aupdate(
                async_key1="async_value1", async_key2="async_value2"
            )

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.dict_field == {}

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.dict_field == {
            "async_key1": "async_value1",
            "async_key2": "async_value2",
        }

    @pytest.mark.asyncio
    async def test_setitem_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.dict_field["direct_key"] = "direct_value"

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.dict_field == {}

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.dict_field == {"direct_key": "direct_value"}

    @pytest.mark.asyncio
    async def test_aset_item_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            await redis_model.dict_field.aset_item("async_key", "async_value")

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.dict_field == {}

        # Assert - changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.dict_field == {"async_key": "async_value"}

    @pytest.mark.asyncio
    async def test_mixed_operations_changes_preserved_during_pipeline_committed_after_edge_case(
        self,
    ):
        # Arrange
        model = AllTypesModel()
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.dict_field.update({"sync_key": "sync_value"})
            await redis_model.dict_field.aset_item("async_key", "async_value")
            redis_model.dict_field["direct_key"] = "direct_value"
            await redis_model.dict_field.aupdate(another_key="another_value")

            # Assert - changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.dict_field == {}

        # Assert - all changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.dict_field["sync_key"] == "sync_value"
        assert final_model.dict_field["async_key"] == "async_value"
        assert final_model.dict_field["direct_key"] == "direct_value"
        assert final_model.dict_field["another_key"] == "another_value"


class TestPipelineBoolField:
    @pytest.mark.asyncio
    async def test_assignment_changes_not_persisted_without_save_edge_case(self):
        # Arrange
        model = AllTypesModel(bool_field=False)
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            redis_model.bool_field = True

            # Assert - boolean changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.bool_field is False

        # Assert - boolean assignment without save() is not committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert (
            final_model.bool_field is False
        )  # Assignment without save() doesn't persist


class TestPipelineCrossType:
    @pytest.mark.asyncio
    async def test_multiple_types_all_changes_preserved_during_pipeline_committed_after_sanity(
        self,
    ):
        # Arrange
        model = AllTypesModel(str_field="start", int_field=10)
        await model.save()

        # Act
        async with model.pipeline() as redis_model:
            # String operations
            redis_model.str_field += "_modified"

            # Integer operations
            redis_model.int_field += 15

            # List operations
            await redis_model.list_field.aappend("list_item")
            redis_model.list_field.extend(["extend1", "extend2"])

            # Dict operations
            await redis_model.dict_field.aset_item("dict_key", "dict_value")
            redis_model.dict_field.update({"update_key": "update_value"})

            # Assert - all changes not visible in Redis during pipeline
            loaded_during_pipeline = await AllTypesModel.get(model.key)
            assert loaded_during_pipeline.str_field == "start"
            assert loaded_during_pipeline.int_field == 10
            assert loaded_during_pipeline.list_field == []
            assert loaded_during_pipeline.dict_field == {}

        # Assert - all changes committed after pipeline
        final_model = await AllTypesModel.get(model.key)
        assert final_model.str_field == "start_modified"
        assert final_model.int_field == 25
        assert "list_item" in final_model.list_field
        assert "extend1" in final_model.list_field
        assert "extend2" in final_model.list_field
        assert final_model.dict_field["dict_key"] == "dict_value"
        assert final_model.dict_field["update_key"] == "update_value"
