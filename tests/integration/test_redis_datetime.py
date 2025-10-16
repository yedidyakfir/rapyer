import pytest
import pytest_asyncio
from datetime import datetime, timezone

from pydantic import Field

from redis_pydantic.base import BaseRedisModel


class DatetimeModel(BaseRedisModel):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DatetimeListModel(BaseRedisModel):
    dates: list[datetime] = Field(default_factory=list)


class DatetimeDictModel(BaseRedisModel):
    event_dates: dict[str, datetime] = Field(default_factory=dict)


@pytest_asyncio.fixture
async def real_redis_client(redis_client):
    DatetimeModel.Meta.redis = redis_client
    DatetimeListModel.Meta.redis = redis_client
    DatetimeDictModel.Meta.redis = redis_client
    yield redis_client
    await redis_client.aclose()


date_values = [
    datetime(2023, 1, 1, 12, 0, 0),
    datetime(2023, 12, 31, 23, 59, 59),
    datetime(2023, 6, 15, 10, 30, 45, 123456),
    datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
]


@pytest.mark.parametrize("test_values", date_values)
@pytest.mark.asyncio
async def test_redis_datetime_set_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = DatetimeModel()
    await model.save()

    # Act
    await model.created_at.set(test_values)

    # Assert
    fresh_model = DatetimeModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.created_at.load()
    assert loaded_value == test_values


@pytest.mark.parametrize("test_values", date_values)
@pytest.mark.asyncio
async def test_redis_datetime_load_functionality_sanity(real_redis_client, test_values):
    # Arrange
    model = DatetimeModel()
    await model.save()
    await model.created_at.set(test_values)

    # Act
    fresh_model = DatetimeModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.created_at.load()

    # Assert
    assert loaded_value == test_values


@pytest.mark.asyncio
async def test_redis_datetime_load_with_none_value_edge_case(real_redis_client):
    # Arrange
    model = DatetimeModel()

    # Act
    loaded_value = await model.created_at.load()

    # Assert
    assert loaded_value is None


@pytest.mark.asyncio
async def test_redis_datetime_set_none_functionality_edge_case(real_redis_client):
    # Arrange
    model = DatetimeModel()
    await model.save()

    # Act
    await model.created_at.set(None)

    # Assert
    fresh_model = DatetimeModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.created_at.load()
    assert loaded_value is None


@pytest.mark.parametrize(
    "redis_values", ["2023-01-01T12:00:00", "invalid_date", 42, True, None]
)
@pytest.mark.asyncio
async def test_redis_datetime_load_type_conversion_edge_case(
    real_redis_client, redis_values
):
    # Arrange
    model = DatetimeModel()
    await model.save()
    await real_redis_client.json().set(
        model.key, model.created_at.json_path, redis_values
    )

    # Act
    fresh_model = DatetimeModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.created_at.load()

    # Assert
    if redis_values == "2023-01-01T12:00:00":
        assert loaded_value == datetime(2023, 1, 1, 12, 0, 0)
    elif redis_values == "invalid_date":
        assert loaded_value is None
    elif redis_values == 42:
        assert loaded_value is None
    elif redis_values == True:
        assert loaded_value is None
    elif redis_values is None:
        assert loaded_value is None


@pytest.mark.asyncio
async def test_redis_datetime_set_with_wrong_type_edge_case(real_redis_client):
    # Arrange
    model = DatetimeModel()

    # Act & Assert
    with pytest.raises(TypeError, match="Value must be datetime or None"):
        await model.created_at.set("2023-01-01")


@pytest.mark.asyncio
async def test_redis_datetime_serialization_functionality_sanity(real_redis_client):
    # Arrange
    test_datetime = datetime(2023, 6, 15, 10, 30, 45, 123456)
    model = DatetimeModel()
    await model.save()

    # Act
    await model.created_at.set(test_datetime)

    # Assert
    raw_value = await real_redis_client.json().get(
        model.key, model.created_at.json_path
    )
    assert raw_value[0] == test_datetime.isoformat()


@pytest.mark.asyncio
async def test_redis_datetime_clone_functionality_sanity(real_redis_client):
    # Arrange
    test_datetime = datetime(2023, 1, 1, 12, 0, 0)
    model = DatetimeModel(created_at=test_datetime)

    # Act
    cloned_datetime = model.created_at.clone()

    # Assert
    assert cloned_datetime == test_datetime
    assert not hasattr(cloned_datetime, "redis_key")


@pytest.mark.asyncio
async def test_redis_datetime_model_creation_functionality_sanity(real_redis_client):
    # Arrange & Act
    model = DatetimeModel()

    # Assert
    from redis_pydantic.types.datetime import RedisDatetime

    assert isinstance(model.created_at, RedisDatetime)
    assert hasattr(model.created_at, "redis_key")
    assert hasattr(model.created_at, "field_path")
    assert hasattr(model.created_at, "redis")
    assert hasattr(model.created_at, "json_path")
    assert model.created_at.redis_key == model.key
    assert model.created_at.field_path == "created_at"
    assert model.created_at.json_path == "$.created_at"
    assert model.created_at.redis == real_redis_client


@pytest.mark.asyncio
async def test_redis_datetime_persistence_across_instances_edge_case(real_redis_client):
    # Arrange
    test_datetime = datetime(2023, 1, 1, 12, 0, 0)
    model1 = DatetimeModel()
    await model1.save()
    await model1.created_at.set(test_datetime)

    # Act
    model2 = DatetimeModel()
    model2.pk = model1.pk
    loaded_value = await model2.created_at.load()

    # Assert
    assert loaded_value == test_datetime


@pytest.mark.parametrize(
    "test_dates",
    [
        [datetime(2023, 1, 1), datetime(2023, 6, 15), datetime(2023, 12, 31)],
        [datetime(2023, 1, 1, 12, 30, 45, 123456)],
        [],
    ],
)
@pytest.mark.asyncio
async def test_redis_datetime_list_functionality_sanity(real_redis_client, test_dates):
    # Arrange
    model = DatetimeListModel(dates=test_dates)
    await model.save()

    # Act
    fresh_model = DatetimeListModel()
    fresh_model.pk = model.pk
    await fresh_model.load()

    # Assert
    assert fresh_model.dates == test_dates


@pytest.mark.parametrize(
    "test_date_dict",
    [
        {"start": datetime(2023, 1, 1), "end": datetime(2023, 12, 31)},
        {"created": datetime(2023, 6, 15, 10, 30, 45, 123456)},
        {},
    ],
)
@pytest.mark.asyncio
async def test_redis_datetime_dict_functionality_sanity(
    real_redis_client, test_date_dict
):
    # Arrange
    model = DatetimeDictModel(event_dates=test_date_dict)
    await model.save()

    # Act
    fresh_model = DatetimeDictModel()
    fresh_model.pk = model.pk
    await fresh_model.load()

    # Assert
    assert fresh_model.event_dates == test_date_dict


@pytest.mark.asyncio
async def test_redis_datetime_isoformat_compatibility_edge_case(real_redis_client):
    # Arrange
    test_datetime = datetime(2023, 6, 15, 10, 30, 45, 123456)
    model = DatetimeModel()
    await model.save()

    # Manually set the ISO format string in Redis
    await real_redis_client.json().set(
        model.key, model.created_at.json_path, test_datetime.isoformat()
    )

    # Act
    fresh_model = DatetimeModel()
    fresh_model.pk = model.pk
    loaded_value = await fresh_model.created_at.load()

    # Assert
    assert loaded_value == test_datetime


@pytest.mark.parametrize("test_datetime", date_values)
@pytest.mark.asyncio
async def test_redis_datetime_model_save_load_sanity(real_redis_client, test_datetime):
    # Arrange
    model = DatetimeModel(created_at=test_datetime)
    await model.save()

    # Act
    loaded_model = await DatetimeModel.get(model.key)

    # Assert
    assert loaded_model.created_at == test_datetime
    assert loaded_model.updated_at == test_datetime
