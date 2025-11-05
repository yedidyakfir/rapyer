import pytest

from tests.models.inheritance_types import AdminUserModel


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["initial_values", "update_values"],
    [
        [{"name": "John", "age": 25}, {"name": "Jane", "age": 30}],
        [
            {"admin_level": 1, "is_super_admin": False},
            {"admin_level": 5, "is_super_admin": True},
        ],
        [
            {"email": "old@test.com", "backup_email": "backup@test.com"},
            {"email": "new@test.com", "backup_email": "newbackup@test.com"},
        ],
    ],
)
async def test_aupdate_function__update_multiple_fields__values_updated_sanity(
    initial_values: dict, update_values: dict
):
    # Arrange
    instance = AdminUserModel(**initial_values)
    await instance.save()

    # Act
    await instance.aupdate(**update_values)

    # Assert
    loaded_instance = await AdminUserModel.get(instance.key)
    for field_name, expected_value in update_values.items():
        assert getattr(loaded_instance, field_name) == expected_value


@pytest.mark.asyncio
async def test_aupdate_function__nested_field_operations__values_persisted_sanity():
    # Arrange
    instance = AdminUserModel(permissions=["read"], managed_users={"user1": "John"})
    await instance.save()

    # Act
    await instance.aupdate(
        permissions=["read", "write", "admin"],
        managed_users={"user1": "John", "user2": "Jane", "user3": "Bob"},
    )

    # Assert
    loaded_instance = await AdminUserModel.get(instance.key)
    assert loaded_instance.permissions == ["read", "write", "admin"]
    assert loaded_instance.managed_users == {
        "user1": "John",
        "user2": "Jane",
        "user3": "Bob",
    }
