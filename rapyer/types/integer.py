from rapyer.types.base import RedisType


class RedisInt(int, RedisType):
    original_type = int

    async def load(self):
        redis_value = await self.client.json().get(self.key, self.field_path)
        return redis_value

    async def set(self, value: int):
        if not isinstance(value, int):
            raise TypeError("Value must be int")

        return await self.client.json().set(self.key, self.json_path, value)

    async def increase(self, amount: int = 1):
        result = await self.client.json().numincrby(self.key, self.json_path, amount)
        return result[0] if isinstance(result, list) and result else result

    def clone(self):
        return int(self)
