import pytest
import pytest_asyncio

from rapyer import init_rapyer
from tests.models.index_types import (
    IndexTestModel,
    UserIndexModel,
    PersonModel,
    AddressModel,
)


@pytest_asyncio.fixture
async def clean_test_indexes(redis_client):
    # Get list of existing indexes before test
    try:
        # Use _list() to get all indexes - this is the internal Redis Search command
        index_list = await redis_client.execute_command("FT._LIST")
        existing_indexes = set(index_list)
    except Exception:
        # If no indexes exist or the command fails, start with an empty set
        existing_indexes = set()

    yield

    # After test: clean up only newly created indexes
    try:
        index_list = await redis_client.execute_command("FT._LIST")
        current_indexes = set(index_list)

        # Delete only indexes created during this test
        new_indexes = current_indexes - existing_indexes
        for index_name in new_indexes:
            try:
                await redis_client.execute_command("FT.DROPINDEX", index_name)
            except Exception:
                # Ignore errors when dropping indexes (might already be deleted)
                pass
    except Exception:
        # If cleanup fails, continue silently to avoid test interference
        pass


@pytest.mark.asyncio
async def test_basic_index_creation(redis_client, clean_test_indexes):
    # Arrange
    models_to_test = [
        {
            "model": IndexTestModel,
            "expected_indexed_fields": {"name": "TEXT", "age": "NUMERIC"},
            "expected_non_indexed_fields": ["description"],
        },
        {
            "model": UserIndexModel,
            "expected_indexed_fields": {
                # Fields from UserIndexModel only (inherited fields not included in same index)
                "username": "TEXT"
            },
            "expected_non_indexed_fields": ["email"],
        },
        {
            "model": PersonModel,
            "expected_indexed_fields": {
                # Only direct fields are indexed, nested model fields are in separate indexes
                "name": "TEXT"
            },
            "expected_non_indexed_fields": ["email"],  # email is a Key, not Index
        },
        {
            "model": AddressModel,
            "expected_indexed_fields": {
                # Nested model has its own index with its indexed fields
                "street": "TEXT",
                "city": "TEXT",
            },
            "expected_non_indexed_fields": [],
        },
    ]

    # Act
    await init_rapyer(redis=redis_client)

    # Assert
    for test_case in models_to_test:
        model = test_case["model"]
        expected_indexed = test_case["expected_indexed_fields"]
        expected_non_indexed = test_case["expected_non_indexed_fields"]

        # Check index exists
        index_name = f"idx:{model.class_key_initials()}"
        info = await redis_client.ft(index_name).info()

        # Verify index was created
        assert info is not None, f"Index not created for {model.__name__}"

        # Extract field information from the index
        fields_in_index = {}
        for attr in info["attributes"]:
            field_name = attr[1]  # Field name
            field_type = attr[5]  # Field type
            fields_in_index[field_name] = field_type

        # Assert indexed fields are present with correct types
        for field_name, expected_type in expected_indexed.items():
            assert (
                field_name in fields_in_index
            ), f"Field '{field_name}' not found in index for {model.__name__}"
            assert (
                fields_in_index[field_name] == expected_type
            ), f"Field '{field_name}' in {model.__name__} expected type '{expected_type}', got '{fields_in_index[field_name]}'"

        # Assert non-indexed fields are not in index
        for field_name in expected_non_indexed:
            assert (
                field_name not in fields_in_index
            ), f"Non-indexed field '{field_name}' found in index for {model.__name__}"


@pytest_asyncio.fixture
async def pre_existing_index(redis_client):
    """
    Fixture that creates a pre-existing index before the test and cleans it up after.
    This simulates an index that existed before our test ran.
    """
    index_name = "idx:test_preserve_index"

    # Create the pre-existing index
    try:
        await redis_client.execute_command(
            "FT.CREATE",
            index_name,
            "ON",
            "JSON",
            "PREFIX",
            "1",
            "test_preserve:",
            "SCHEMA",
            "test_field",
            "TEXT",
        )
    except Exception:
        # Index might already exist from previous test, drop and recreate
        try:
            await redis_client.execute_command("FT.DROPINDEX", index_name)
            await redis_client.execute_command(
                "FT.CREATE",
                index_name,
                "ON",
                "JSON",
                "PREFIX",
                "1",
                "test_preserve:",
                "SCHEMA",
                "test_field",
                "TEXT",
            )
        except Exception:
            pass

    yield index_name

    # Clean up after test
    try:
        await redis_client.execute_command("FT.DROPINDEX", index_name)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_cleanup_preserves_existing_indexes(
    redis_client, pre_existing_index, clean_test_indexes
):
    """
    Test that the cleanup fixture preserves indexes that existed before the test.
    """
    # Arrange - Verify the pre-existing index exists
    try:
        info = await redis_client.execute_command("FT.INFO", pre_existing_index)
        assert info is not None, "Pre-existing index not found"
    except Exception:
        pytest.fail("Pre-existing index not found")

    # Act - Run init_rapyer which creates new indexes
    await init_rapyer(redis=redis_client)

    # At this point, both the pre-existing index and new rapyer indexes should exist
    # When the clean_test_indexes fixture cleans up, it should only remove the new ones

    # Assert - Verify the pre-existing index still exists
    try:
        info = await redis_client.execute_command("FT.INFO", pre_existing_index)
        assert info is not None, "Pre-existing index was incorrectly deleted by cleanup"
    except Exception:
        pytest.fail("Pre-existing index was incorrectly deleted by cleanup")
