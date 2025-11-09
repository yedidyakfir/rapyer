import pytest

from tests.models.common import UserWithKeyModel


@pytest.mark.asyncio
async def test_store_and_load_user_with_key_annotation_sanity():
    # Arrange
    user_id = "user123"
    original_user = UserWithKeyModel(
        user_id=user_id, name="John Doe", email="john.doe@example.com", age=30
    )

    # Act
    await original_user.save()
    loaded_user = await UserWithKeyModel.get(original_user.key)

    # Assert
    assert loaded_user == original_user
    assert loaded_user.pk == user_id
