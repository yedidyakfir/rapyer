import copy
from datetime import datetime
from rapyer.types.base import RedisType, RedisSerializer


class DatetimeSerializer(RedisSerializer):
    def serialize_value(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def deserialize_value(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None


class RedisDatetime(datetime, RedisType):
    serializer = DatetimeSerializer(datetime, None)

    def __new__(cls, value=None, *args, **kwargs):
        return super().__new__(
            cls,
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            value.tzinfo,
        )

    def __init__(self, *args, **kwargs):
        datetime.__init__(self)
        RedisType.__init__(self, **kwargs)

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        if redis_value is not None:
            return self.serializer.deserialize_value(redis_value)
        return None

    async def set(self, value: datetime):
        if value is not None and not isinstance(value, datetime):
            raise TypeError("Value must be datetime or None")

        serialized_value = self.serializer.serialize_value(value)
        return await self.client.json().set(
            self.redis_key, self.json_path, serialized_value
        )

    def clone(self):
        return datetime.fromtimestamp(self.timestamp())
