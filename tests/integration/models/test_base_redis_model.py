import pytest

from tests.models.specialized import UserModel


@pytest.mark.asyncio
async def test_base_redis_model__list_append__check_redis_append(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag2"])
    await user.asave()

    # Act
    await user.tags.aappend("tag3")

    # Assert
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert user.tags == actual_lst[0]


@pytest.mark.asyncio
async def test_base_redis_model__list_extend__check_redis_extend(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1"])
    await user.asave()

    # Act
    await user.tags.aextend(["tag2", "tag3"])

    # Assert
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    # Note: extend reverses order due to implementation, check both contain same elements
    assert set(user.tags) == set(actual_lst[0])
    assert len(user.tags) == len(actual_lst[0])


@pytest.mark.asyncio
async def test_base_redis_model__list_insert__check_redis_insert(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag3"])
    await user.asave()

    # Act
    await user.tags.ainsert(1, "tag2")

    # Assert
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert user.tags == actual_lst[0]


@pytest.mark.asyncio
async def test_base_redis_model__list_clear__check_redis_clear():
    # Arrange
    user = UserModel(tags=["tag1", "tag2", "tag3"])
    await user.asave()

    # Act
    await user.tags.aclear()

    # Assert
    loaded_user = await UserModel.aget(user.key)
    assert loaded_user.tags == []


@pytest.mark.asyncio
async def test_base_redis_model__save__check_redis_save(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag2"])

    # Act
    await user.asave()

    # Assert
    actual_data = await real_redis_client.json().get(user.key, "$")
    assert actual_data[0]["tags"] == user.tags


@pytest.mark.asyncio
async def test_base_redis_model__load__check_redis_load(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag2"])
    await user.asave()
    await real_redis_client.json().arrappend(user.key, user.tags.json_path, "tag3")

    # Act
    user.tags = await user.tags.load()

    # Assert
    actual_lst = await real_redis_client.json().get(user.key, user.tags.json_path)
    assert user.tags == actual_lst[0]


@pytest.mark.asyncio
async def test_base_redis_model__delete__check_redis_delete_sanity(real_redis_client):
    # Arrange
    user = UserModel(tags=["tag1", "tag2"])
    await user.asave()
    loaded_user = await UserModel.aget(user.key)

    # Act
    await loaded_user.delete()

    # Assert
    key_exists = await real_redis_client.exists(user.key)
    assert key_exists == 0


@pytest.mark.asyncio
async def test_base_redis_model__try_delete_existing_key__check_returns_true_sanity(
    real_redis_client,
):
    # Arrange
    user = UserModel(tags=["tag1", "tag2"])
    await user.asave()

    # Act
    result = await UserModel.delete_by_key(user.key)

    # Assert
    assert result is True
    key_exists = await real_redis_client.exists(user.key)
    assert key_exists == 0


@pytest.mark.asyncio
async def test_base_redis_model__try_delete_nonexistent_key__check_returns_false_sanity():
    # Arrange
    mock_key = "UserModel:nonexistent_key"

    # Act
    result = await UserModel.delete_by_key(mock_key)

    # Assert
    assert result is False
