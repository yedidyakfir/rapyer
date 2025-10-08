from redis_pydantic.types.base import RedisType


class RedisStr(str, RedisType):
    def __new__(cls, value="", **kwargs):
        if value is None:
            value = ""
        return super().__new__(cls, value)

    def __init__(self, value="", **kwargs):
        RedisType.__init__(self, **kwargs)

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        if redis_value is not None:
            if isinstance(redis_value, str):
                return redis_value
            elif isinstance(redis_value, bytes):
                return redis_value.decode()
            else:
                return str(redis_value)
        return ""

    async def set(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Value must be str")

        return await self.client.json().set(self.redis_key, self.json_path, value)

    def clone(self):
        return str(self)
