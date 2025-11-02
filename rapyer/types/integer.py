from rapyer.types.base import RedisType


class RedisInt(int, RedisType):
    original_type = int

    async def increase(self, amount: int = 1):
        result = await self.client.json().numincrby(self.key, self.json_path, amount)
        return result[0] if isinstance(result, list) and result else result

    def clone(self):
        return int(self)
