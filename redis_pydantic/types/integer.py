from redis_pydantic.types.base import RedisType


class RedisInt(int, RedisType):
    def __new__(cls, value=0, **kwargs):
        if value is None:
            value = 0
        return super().__new__(cls, value)

    def __init__(self, value=0, **kwargs):
        RedisType.__init__(self, **kwargs)

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        if redis_value is not None:
            if isinstance(redis_value, (int, float)):
                return int(redis_value)
            elif isinstance(redis_value, str):
                try:
                    return int(redis_value)
                except ValueError:
                    return 0
            else:
                return 0
        return 0

    async def set(self, value: int):
        if not isinstance(value, int):
            raise TypeError("Value must be int")

        return await self.client.json().set(self.redis_key, self.json_path, value)

    def clone(self):
        return int(self)

    def deserialize_value(self, value):
        return int(value)
