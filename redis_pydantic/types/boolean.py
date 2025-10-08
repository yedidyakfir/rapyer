from redis_pydantic.types.base import RedisType


class RedisBool(int, RedisType):
    def __new__(cls, value=False, **kwargs):
        if value is None:
            value = False
        return super().__new__(cls, bool(value))

    def __init__(self, value=False, **kwargs):
        RedisType.__init__(self, **kwargs)

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        if redis_value is not None:
            if isinstance(redis_value, bool):
                return redis_value
            elif isinstance(redis_value, (int, float)):
                return bool(redis_value)
            elif isinstance(redis_value, str):
                return redis_value.lower() in ("true", "1")
            else:
                return bool(redis_value)
        return False

    async def set(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("Value must be bool")

        return await self.client.json().set(self.redis_key, self.json_path, value)

    def clone(self):
        return bool(self)

    def deserialize_value(self, value):
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ("true", "1")
        else:
            return bool(value)
