import pytest

from rapyer import init_rapyer
from tests.models.index_types import IndexTestModel, UserIndexModel, PersonModel, AddressModel


@pytest.mark.asyncio
async def test_basic_index_creation(redis_client):
    # Arrange
    models_to_test = [
        {
            "model": IndexTestModel,
            "expected_indexed_fields": {
                "name": "TEXT",
                "age": "NUMERIC"
            },
            "expected_non_indexed_fields": ["description"]
        },
        {
            "model": UserIndexModel,
            "expected_indexed_fields": {
                # Fields from UserIndexModel only (inherited fields not included in same index)
                "username": "TEXT"
            },
            "expected_non_indexed_fields": ["email"]
        },
        {
            "model": PersonModel,
            "expected_indexed_fields": {
                # Only direct fields are indexed, nested model fields are in separate indexes
                "name": "TEXT"
            },
            "expected_non_indexed_fields": ["email"]  # email is a Key, not Index
        },
        {
            "model": AddressModel,
            "expected_indexed_fields": {
                # Nested model has its own index with its indexed fields
                "street": "TEXT",
                "city": "TEXT"
            },
            "expected_non_indexed_fields": []
        }
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
            assert field_name in fields_in_index, f"Field '{field_name}' not found in index for {model.__name__}"
            assert fields_in_index[field_name] == expected_type, f"Field '{field_name}' in {model.__name__} expected type '{expected_type}', got '{fields_in_index[field_name]}'"

        # Assert non-indexed fields are not in index
        for field_name in expected_non_indexed:
            assert field_name not in fields_in_index, f"Non-indexed field '{field_name}' found in index for {model.__name__}"
