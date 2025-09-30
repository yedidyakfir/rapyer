import pytest
from pydantic import Field

from redis_pydantic.base import RedisModel


class UserModel(RedisModel):
    name: str
    age: int
    is_active: bool = True
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    counter: int = 0


@pytest.mark.asyncio
async def test_save_and_get_sanity(redis_client):
    # Arrange
    user = UserModel(
        name="John", age=30, tags=["developer", "python"], metadata={"role": "admin"}
    )

    # Act
    saved_user = await user.save()
    retrieved_user = await UserModel.get(user.key)

    # Assert
    assert saved_user == retrieved_user


@pytest.mark.asyncio
async def test_redis_keys_created_sanity(redis_client):
    # Arrange
    user = UserModel(name="Jane", age=25, tags=["python"], metadata={"role": "user"})

    # Act
    await user.save()
    all_keys = await redis_client.keys("*")

    # Assert
    decoded_keys = [key.decode() if isinstance(key, bytes) else key for key in all_keys]
    user_keys = [key for key in decoded_keys if key.startswith(user.key)]
    assert len(user_keys) > 0

    expected_keys = [
        f"{user.key}/name",
        f"{user.key}/age",
        f"{user.key}/is_active",
        f"{user.key}/tags",
        f"{user.key}/metadata",
    ]

    for expected_key in expected_keys:
        assert expected_key in decoded_keys


@pytest.mark.asyncio
async def test_update_model_sanity(redis_client):
    # Arrange
    user = UserModel(
        name="Alice", age=28, tags=["manager"], metadata={"role": "team_lead"}
    )
    await user.save()

    # Act
    await user.update(name="Alice Smith", age=29, tags=["manager", "senior"])

    # Assert
    retrieved_user = await UserModel.get(user.key)
    assert retrieved_user.name == "Alice Smith"
    assert retrieved_user.age == 29
    assert retrieved_user.tags == ["manager", "senior"]
    assert retrieved_user.metadata == {"role": "team_lead"}


@pytest.mark.asyncio
async def test_update_unsaved_model_edge_case(redis_client):
    # Arrange
    user = UserModel(name="Bob", age=35, tags=["developer"])

    # Act
    await user.update(name="Bob Updated", age=36)

    # Assert
    all_keys = await redis_client.keys("*")
    decoded_keys = [key.decode() if isinstance(key, bytes) else key for key in all_keys]
    user_keys = [key for key in decoded_keys if key.startswith(user.key)]
    assert len(user_keys) == 0


@pytest.mark.asyncio
async def test_delete_from_key_sanity(redis_client):
    # Arrange
    user = UserModel(
        name="John", age=30, tags=["developer", "python"], metadata={"role": "admin"}
    )
    await user.save()

    all_keys_before = await redis_client.keys("*")
    user_keys_before = [
        key for key in all_keys_before if key.decode().startswith(user.key)
    ]
    assert len(user_keys_before) > 0

    # Act
    await UserModel.delete_from_key(user.key)

    # Assert
    all_keys_after = await redis_client.keys("*")
    user_keys_after = [
        key for key in all_keys_after if key.decode().startswith(user.key)
    ]
    assert len(user_keys_after) == 0


@pytest.mark.asyncio
async def test_delete_model_sanity(redis_client):
    # Arrange
    user = UserModel(
        name="Sarah",
        age=32,
        tags=["manager", "team_lead"],
        metadata={"department": "engineering"},
    )
    await user.save()

    all_keys_before = await redis_client.keys("*")
    user_keys_before = [
        key for key in all_keys_before if key.decode().startswith(user.key)
    ]
    assert len(user_keys_before) > 0

    # Act
    await user.delete()

    # Assert
    all_keys_after = await redis_client.keys("*")
    decoded_keys = [
        key.decode() if isinstance(key, bytes) else key for key in all_keys_after
    ]
    user_keys_after = [key for key in decoded_keys if key.startswith(user.key)]
    assert len(user_keys_after) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("counter_value, increment", [(0, 1), (5, 3), (10, -2)])
async def test_increase_counter_sanity(redis_client, counter_value, increment):
    # Arrange
    user = UserModel(name="Counter Test", age=25, counter=counter_value)
    await user.save()

    # Act
    await user.increase_counter("counter", increment)

    # Assert
    retrieved_user = await UserModel.get(user.key)
    assert retrieved_user.counter == counter_value + increment
    assert user.counter == counter_value + increment


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "initial_tags, new_tag",
    [([], "first_tag"), (["existing"], "new_tag"), (["one", "two"], "three")],
)
async def test_append_to_list_sanity(redis_client, initial_tags, new_tag):
    # Arrange
    user = UserModel(name="List Test", age=25, tags=initial_tags)
    await user.save()

    # Act
    await user.append_to_list("tags", new_tag)

    # Assert
    retrieved_user = await UserModel.get(user.key)
    expected_tags = [new_tag] + initial_tags
    assert retrieved_user.tags == expected_tags
    assert user.tags == expected_tags


@pytest.mark.asyncio
async def test_increase_counter_race_condition(redis_client):
    # Arrange
    user = UserModel(name="Race Test", age=25, counter=10)
    await user.save()

    # Act - simulate race condition: modify local model but not in Redis
    user.counter = 100  # Local change not reflected in Redis
    await user.increase_counter("counter", 5)

    # Assert
    retrieved_user = await UserModel.get(user.key)
    assert retrieved_user.counter == 15  # Redis value (10) + increment (5)
    assert user.counter == 105  # Local value (100) + increment (5)


@pytest.mark.asyncio
async def test_append_to_list_race_condition(redis_client):
    # Arrange
    user = UserModel(name="Race Test", age=25, tags=["initial"])
    await user.save()

    # Act - simulate race condition: modify local model but not in Redis
    user.tags = ["local_change"]  # Local change not reflected in Redis
    await user.append_to_list("tags", "new_item")

    # Assert
    retrieved_user = await UserModel.get(user.key)
    assert retrieved_user.tags == ["new_item", "initial"]  # Redis value + new item
    assert user.tags == ["new_item", "local_change"]  # Local value + new item
