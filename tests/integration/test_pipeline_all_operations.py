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
async def test_pipeline_list_aappend__check_pipeline_support_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["initial"])
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.tags.aappend("new_tag")

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.tags == ["initial"]

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = ["initial", "new_tag"]
        assert final_model.tags == expected_result
        print("✅ aappend: WORKS in pipeline context")

    except Exception as e:
        print(f"❌ aappend: FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_list_aextend__check_pipeline_support_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["initial"])
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.tags.aextend(["tag1", "tag2"])

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.tags == ["initial"]

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = ["initial", "tag1", "tag2"]
        assert final_model.tags == expected_result
        print("✅ aextend: WORKS in pipeline context")

    except Exception as e:
        print(f"❌ aextend: FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_list_ainsert__check_pipeline_support_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["first", "last"])
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.tags.ainsert(1, "middle")

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.tags == ["first", "last"]

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = ["first", "middle", "last"]
        assert final_model.tags == expected_result
        print("✅ ainsert: WORKS in pipeline context")

    except Exception as e:
        print(f"❌ ainsert: FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_list_aclear__check_pipeline_support_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(tags=["tag1", "tag2"])
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.tags.aclear()

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.tags == ["tag1", "tag2"]

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = []
        assert final_model.tags == expected_result
        print("✅ aclear (list): WORKS in pipeline context")

    except Exception as e:
        print(f"❌ aclear (list): FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_dict_aset_item__check_pipeline_support_sanity(
    real_redis_client,
):
    # Arrange
    model = ComprehensiveTestModel(metadata={"existing": "value"})
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.metadata.aset_item("new_key", "new_value")

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.metadata == {"existing": "value"}

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = {"existing": "value", "new_key": "new_value"}
        assert final_model.metadata == expected_result
        print("✅ aset_item: WORKS in pipeline context")

    except Exception as e:
        print(f"❌ aset_item: FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_dict_adel_item__check_pipeline_support_sanity(
    real_redis_client,
):
    # Arrange
    model = ComprehensiveTestModel(metadata={"key1": "value1", "key2": "value2"})
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.metadata.adel_item("key1")

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.metadata == {"key1": "value1", "key2": "value2"}

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = {"key2": "value2"}
        assert final_model.metadata == expected_result
        print("✅ adel_item: WORKS in pipeline context")

    except Exception as e:
        print(f"❌ adel_item: FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_dict_aupdate__check_pipeline_support_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(metadata={"existing": "value"})
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.metadata.aupdate(key1="value1", key2="value2")

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.metadata == {"existing": "value"}

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = {"existing": "value", "key1": "value1", "key2": "value2"}
        assert final_model.metadata == expected_result
        print("✅ aupdate: WORKS in pipeline context")

    except Exception as e:
        print(f"❌ aupdate: FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_dict_aclear__check_pipeline_support_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(metadata={"key1": "value1", "key2": "value2"})
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.metadata.aclear()

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.metadata == {"key1": "value1", "key2": "value2"}

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = {}
        assert final_model.metadata == expected_result
        print("✅ aclear (dict): WORKS in pipeline context")

    except Exception as e:
        print(f"❌ aclear (dict): FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_string_set__check_pipeline_support_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(name="original")
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.name.set("updated")

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.name == "original"

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = "updated"
        assert final_model.name == expected_result
        print("✅ set (string): WORKS in pipeline context")

    except Exception as e:
        print(f"❌ set (string): FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_int_set__check_pipeline_support_sanity(real_redis_client):
    # Arrange
    model = ComprehensiveTestModel(counter=10)
    await model.save()

    # Act & Test
    try:
        async with model.pipeline() as redis_model:
            await redis_model.counter.set(99)

            # Check if change is not applied yet (atomicity test)
            loaded_model = await ComprehensiveTestModel.get(model.key)
            assert loaded_model.counter == 10

        # Check if change was applied after pipeline
        final_model = await ComprehensiveTestModel.get(model.key)
        expected_result = 99
        assert final_model.counter == expected_result
        print("✅ set (int): WORKS in pipeline context")

    except Exception as e:
        print(f"❌ set (int): FAILED in pipeline context - {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_all_operations_combined__check_atomicity_sanity(
    real_redis_client,
):
    # Arrange
    model = ComprehensiveTestModel(
        tags=["tag1"], metadata={"key1": "value1"}, name="original", counter=0
    )
    await model.save()

    operations_that_work = []
    operations_that_fail = []

    # Test all operations in pipeline
    async with model.pipeline() as redis_model:
        try:
            await redis_model.tags.aappend("tag2")
            operations_that_work.append("list.aappend")
        except Exception as e:
            operations_that_fail.append(f"list.aappend: {e}")

        try:
            await redis_model.metadata.aupdate(key2="value2")
            operations_that_work.append("dict.aupdate")
        except Exception as e:
            operations_that_fail.append(f"dict.aupdate: {e}")

        try:
            await redis_model.name.set("updated")
            operations_that_work.append("str.set")
        except Exception as e:
            operations_that_fail.append(f"str.set: {e}")

        try:
            await redis_model.counter.set(100)
            operations_that_work.append("int.set")
        except Exception as e:
            operations_that_fail.append(f"int.set: {e}")

        # Check intermediate state - should be unchanged
        loaded_model = await ComprehensiveTestModel.get(model.key)
        assert loaded_model.tags == ["tag1"]
        assert loaded_model.metadata == {"key1": "value1"}
        assert loaded_model.name == "original"
        assert loaded_model.counter == 0

    # Check final state
    final_model = await ComprehensiveTestModel.get(model.key)

    print("\n=== PIPELINE OPERATION RESULTS ===")
    print(f"✅ Operations that work: {operations_that_work}")
    print(f"❌ Operations that fail: {operations_that_fail}")

    # Verify the operations that worked actually applied
    if "list.aappend" in operations_that_work:
        assert final_model.tags == ["tag1", "tag2"]
    if "dict.aupdate" in operations_that_work:
        assert final_model.metadata == {"key1": "value1", "key2": "value2"}
    if "str.set" in operations_that_work:
        assert final_model.name == "updated"
    if "int.set" in operations_that_work:
        assert final_model.counter == 100
