from datetime import datetime
import pytest

from tests.models.common import UserWithKeyModel, EventWithDatetimeKeyModel


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


@pytest.mark.asyncio
async def test_store_and_load_event_with_datetime_key_annotation_sanity():
    # Arrange
    created_at = datetime(2023, 12, 25, 10, 30, 45)
    original_event = EventWithDatetimeKeyModel(
        created_at=created_at,
        event_name="Christmas Meeting",
        description="Annual holiday planning meeting",
        duration_minutes=90
    )

    # Act
    await original_event.save()
    loaded_event = await EventWithDatetimeKeyModel.get(original_event.key)

    # Assert
    assert loaded_event == original_event
    assert loaded_event.pk == created_at
