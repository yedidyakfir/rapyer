from rapyer.types.base import RedisType


class RedisStr(str, RedisType):
    original_type = str

    async def load(self):
        redis_value = await self.client.json().get(self.key, self.field_path)
        return redis_value

    async def set(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Value must be str")

        return await self.client.json().set(self.key, self.json_path, value)

    def clone(self):
        return str(self)
