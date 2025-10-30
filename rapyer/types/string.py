from rapyer.types.base import RedisType


class RedisStr(str, RedisType):
    original_type = str

    async def load(self):
        redis_value = await self.client.json().get(self.key, self.field_path)
        return redis_value


    def clone(self):
        return str(self)
