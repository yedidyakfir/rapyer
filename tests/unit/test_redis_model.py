import pytest
from pydantic import Field

from redis_pydantic.base import RedisModel


class UserModel(RedisModel):
    name: str
    age: int
    is_active: bool = True
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


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
