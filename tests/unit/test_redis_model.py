import pytest
from typing import List, Dict
from redis_pydantic.base import RedisModel


class UserModel(RedisModel):
    name: str
    age: int
    is_active: bool = True
    tags: List[str] = []
    metadata: Dict[str, str] = {}


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
    assert saved_user == user
    assert retrieved_user.name == user.name
    assert retrieved_user.age == user.age
    assert retrieved_user.is_active == user.is_active
    assert set(retrieved_user.tags) == set(user.tags)
    assert retrieved_user.metadata == user.metadata
    assert retrieved_user.pk == user.pk


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
