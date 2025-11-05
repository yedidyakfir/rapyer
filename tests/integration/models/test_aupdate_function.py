import pytest

from rapyer import RedisStr
from tests.models.inheritance_types import AdminUserModel
from tests.models.pickle_types import ModelWithUnserializableFields


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["initial_values", "update_values"],
    [
        [
            {"name": "John", "age": 25, "email": "john@test.com", "admin_level": 3},
            {"name": "Jane", "age": 30},
        ],
        [
            {
                "admin_level": 1,
                "is_super_admin": False,
                "name": "Admin",
                "email": "admin@test.com",
            },
            {"admin_level": 5, "is_super_admin": True},
        ],
        [
            {
                "email": "old@test.com",
                "backup_email": "backup@test.com",
                "name": "TestUser",
                "age": 35,
            },
            {"email": "new@test.com", "backup_email": "newbackup@test.com"},
        ],
    ],
)
async def test_aupdate_function__update_multiple_fields__values_updated_and_unchanged_fields_preserved_sanity(
    initial_values: dict, update_values: dict
):
    # Arrange
    instance = AdminUserModel(**initial_values)
    await instance.save()
    original_data = instance.model_dump()

    # Act
    await instance.aupdate(**update_values)

    # Assert
    loaded_instance = await AdminUserModel.get(instance.key)
    # Check updated fields
    for field_name, expected_value in update_values.items():
        assert getattr(loaded_instance, field_name) == expected_value
    # Check unchanged fields - all fields not in update_values should remain the same
    for field_name in AdminUserModel.model_fields.keys():
        if field_name not in update_values:
            assert getattr(loaded_instance, field_name) == original_data[field_name]


@pytest.mark.asyncio
async def test_aupdate_function__nested_field_operations__values_persisted_and_other_fields_unchanged_sanity():
    # Arrange
    instance = AdminUserModel(
        name="AdminUser",
        email="admin@test.com",
        age=40,
        admin_level=2,
        permissions=["read"],
        managed_users={"user1": "John"},
        is_super_admin=False,
    )
    await instance.save()
    original_data = instance.model_dump()
    update_values = {
        "permissions": ["read", "write", "admin"],
        "managed_users": {"user1": "John", "user2": "Jane", "user3": "Bob"},
    }

    # Act
    await instance.aupdate(**update_values)

    # Assert
    loaded_instance = await AdminUserModel.get(instance.key)
    # Check updated fields
    for field_name, expected_value in update_values.items():
        assert getattr(loaded_instance, field_name) == expected_value
    # Check unchanged fields - all fields not in update_values should remain the same
    for field_name in AdminUserModel.model_fields.keys():
        if field_name not in update_values:
            assert getattr(loaded_instance, field_name) == original_data[field_name]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["field_name", "initial_value"],
    [
        ["optional_field", "some_value"],
        ["backup_email", "backup@test.com"],
    ],
)
async def test_aupdate_function__update_field_to_none__value_updated_and_other_fields_unchanged_sanity(
    field_name: str, initial_value
):
    # Arrange
    instance = AdminUserModel(
        **{field_name: initial_value, "name": "TestUser", "email": "test@example.com"}
    )
    await instance.save()
    original_data = instance.model_dump()
    update_values = {field_name: None}

    # Act
    await instance.aupdate(**update_values)

    # Assert
    loaded_instance = await AdminUserModel.get(instance.key)
    # Check the updated field is None
    assert getattr(loaded_instance, field_name) is None
    # Check unchanged fields
    for other_field_name in AdminUserModel.model_fields.keys():
        if other_field_name != field_name:
            assert (
                getattr(loaded_instance, other_field_name)
                == original_data[other_field_name]
            )


@pytest.mark.asyncio
async def test_aupdate_function__update_non_redis_supported_types__values_serialized_and_updated_sanity():
    # Arrange
    instance = ModelWithUnserializableFields()
    await instance.save()

    # Act
    await instance.aupdate(model_type=RedisStr, python_type=int)

    # Assert
    loaded_instance = await ModelWithUnserializableFields.get(instance.key)
    # Check updated field - sets and types should be preserved through serialization
    assert loaded_instance.model_type == RedisStr
    assert loaded_instance.python_type == int
