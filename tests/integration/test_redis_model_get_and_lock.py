import asyncio
from datetime import datetime
from typing import List
from unittest.mock import Mock

import pytest
import pytest_asyncio
from pydantic import Field

from rapyer.base import AtomicRedisModel


class RichModel(AtomicRedisModel):
    name: str = ""
    age: int = 0
    tags: List[str] = Field(default_factory=list)
    active: bool = True
    date1: str = ""


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    RichModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


@pytest.mark.asyncio
async def test_redis_model_get_functionality(real_redis_client):
    # Arrange
    original_model = RichModel(
        name="test_user", age=25, tags=["tag1", "tag2"], active=True, date1="2023-01-01"
    )
    await original_model.save()

    # Act
    retrieved_model = await RichModel.get(original_model.key)

    # Assert
    assert retrieved_model.name == original_model.name
    assert retrieved_model.age == original_model.age
    assert retrieved_model.tags == original_model.tags
    assert retrieved_model.active == original_model.active
    assert retrieved_model.date1 == original_model.date1
    assert retrieved_model.pk == original_model.pk


@pytest.mark.asyncio
async def test_redis_model_lock_with_concurrent_access_functionality(real_redis_client):
    # Arrange
    model = RichModel(name="lock_test", date1="initial_date")
    await model.save()

    enter_mock = Mock()
    exit_mock = Mock()

    async def lock_and_modify(model_key: str, delay_seconds: int):
        # Get fresh model instance
        fresh_model = await RichModel.get(model_key)

        async with fresh_model.lock(save_at_end=True) as locked_model:
            current_time = datetime.now().isoformat()
            enter_mock(current_time, locked_model.model_dump())

            await asyncio.sleep(delay_seconds)

            exit_date = datetime.now().isoformat()
            locked_model.date1 = exit_date
            exit_mock(exit_date)

    # Act
    await asyncio.gather(lock_and_modify(model.key, 3), lock_and_modify(model.key, 3))

    # Assert
    assert enter_mock.call_count == 2
    assert exit_mock.call_count == 2

    # Get call arguments
    enter_calls = enter_mock.call_args_list
    exit_calls = exit_mock.call_args_list

    # Extract timestamps
    second_enter_time = datetime.fromisoformat(enter_calls[1][0][0])
    first_exit_time = datetime.fromisoformat(exit_calls[0][0][0])
    second_model_dump = enter_calls[1][0][1]
    second_model_dump = RichModel.model_validate(second_model_dump)

    # The second enter should be after the first exit (sequential execution due to lock)
    assert second_enter_time > first_exit_time
    assert second_model_dump.date1 != "initial_date"


@pytest.mark.asyncio
async def test_redis_model_lock_from_key_functionality(real_redis_client):
    # Arrange
    model = RichModel(name="lock_from_key_test", age=30, date1="initial_date")
    await model.save()

    # Act
    async with RichModel.lock_from_key(model.key, save_at_end=True) as locked_model:
        locked_model.name = "modified_name"
        locked_model.age = 35
        locked_model.date1 = "modified_date"

    # Assert
    retrieved_model = await RichModel.get(model.key)
    assert retrieved_model.name == "modified_name"
    assert retrieved_model.age == 35
    assert retrieved_model.date1 == "modified_date"


@pytest.mark.asyncio
async def test_redis_model_lock_from_key_with_action_functionality(real_redis_client):
    # Arrange
    model = RichModel(name="lock_action_test", tags=["initial"])
    await model.save()

    # Act
    async with RichModel.lock_from_key(
        model.key, "custom_action", save_at_end=True
    ) as locked_model:
        locked_model.tags.append("added_tag")
        locked_model.name = "action_modified"

    # Assert
    retrieved_model = await RichModel.get(model.key)
    assert retrieved_model.name == "action_modified"
    assert "added_tag" in retrieved_model.tags


@pytest.mark.asyncio
async def test_redis_model_lock_from_key_with_concurrent_access_functionality(
    real_redis_client,
):
    # Arrange
    model = RichModel(name="concurrent_lock_from_key", date1="initial_date")
    await model.save()

    enter_mock = Mock()
    exit_mock = Mock()

    async def lock_from_key_and_modify(model_key: str, delay_seconds: int):
        async with RichModel.lock_from_key(model_key, save_at_end=True) as locked_model:
            current_time = datetime.now().isoformat()
            enter_mock(current_time, locked_model.model_dump())

            await asyncio.sleep(delay_seconds)

            exit_date = datetime.now().isoformat()
            locked_model.date1 = exit_date
            exit_mock(exit_date)

    # Act
    await asyncio.gather(
        lock_from_key_and_modify(model.key, 3), lock_from_key_and_modify(model.key, 3)
    )

    # Assert
    assert enter_mock.call_count == 2
    assert exit_mock.call_count == 2

    # Get call arguments
    enter_calls = enter_mock.call_args_list
    exit_calls = exit_mock.call_args_list

    # Extract timestamps
    second_enter_time = datetime.fromisoformat(enter_calls[1][0][0])
    first_exit_time = datetime.fromisoformat(exit_calls[0][0][0])
    second_model_dump = enter_calls[1][0][1]
    second_model_dump = RichModel.model_validate(second_model_dump)

    # The second enter should be after the first exit (sequential execution due to lock)
    assert second_enter_time > first_exit_time
    assert second_model_dump.date1 != "initial_date"


@pytest.mark.asyncio
async def test_redis_model_lock_with_save_at_end_true_saves_changes_functionality(
    real_redis_client,
):
    # Arrange
    model = RichModel(
        name="save_at_end_test", age=25, tags=["initial"], date1="2023-01-01"
    )
    await model.save()

    # Act
    async with RichModel.lock_from_key(model.key, save_at_end=True) as locked_model:
        locked_model.name = "modified_name"
        locked_model.age = 30
        locked_model.tags.append("new_tag")
        locked_model.date1 = "2023-12-31"

    # Assert
    retrieved_model = await RichModel.get(model.key)
    assert retrieved_model.name == "modified_name"
    assert retrieved_model.age == 30
    assert retrieved_model.tags == ["initial", "new_tag"]
    assert retrieved_model.date1 == "2023-12-31"
