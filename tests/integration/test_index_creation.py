import pytest

from rapyer import init_rapyer
from tests.models.index_types import IndexTestModel1


@pytest.mark.asyncio
async def test_basic_index_creation(redis_client):
    # Act
    await init_rapyer(redis=redis_client)

    # Assert - Check index exists
    index_name = f"idx:{IndexTestModel1.class_key_initials()}"
    info = await redis_client.ft(index_name).info()

    # Verify index was created
    assert info is not None

    # Extract field information from index
    fields_in_index = {}
    for attr in info["attributes"]:
        field_name = attr[1]  # Field name
        field_type = attr[3]  # Field type
        fields_in_index[field_name] = field_type

    # Assert indexed fields are present with correct types
    assert "name" in fields_in_index
    assert fields_in_index["name"] == "TEXT"
    assert "age" in fields_in_index
    assert fields_in_index["age"] == "NUMERIC"

    # Assert non-indexed field is not in index
    assert "description" not in fields_in_index
