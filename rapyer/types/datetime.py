from datetime import datetime

from rapyer.types.base import RedisType


class RedisDatetime(datetime, RedisType):
    original_type = datetime

    def __new__(cls, value, *args, **kwargs):
        if isinstance(value, datetime):
            # Support init from a datetime
            return datetime.__new__(cls, *value.timetuple()[:6])
        else:
            return datetime.__new__(cls, value, *args, *kwargs)

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        if redis_value:
            return datetime.fromisoformat(redis_value)
        return None

    async def set(self, value: datetime):
        if value is not None and not isinstance(value, datetime):
            raise TypeError("Value must be datetime or None")

        return await self.client.json().set(
            self.redis_key, self.json_path, value.isoformat()
        )

    def clone(self):
        return datetime.fromtimestamp(self.timestamp())
