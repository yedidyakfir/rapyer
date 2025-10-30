from rapyer.types.base import RedisType


class RedisBool(int, RedisType):
    original_type = bool

    async def load(self):
        redis_value = await self.client.json().get(self.key, self.field_path)
        return redis_value


    def clone(self):
        return bool(self)

    def __repr__(self):
        return f"{bool(self)}"
