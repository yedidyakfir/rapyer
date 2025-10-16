from rapyer.types.base import RedisType, RedisSerializer


class IntegerSerializer(RedisSerializer):
    def serialize_value(self, value):
        return int(value) if value is not None else None

    def deserialize_value(self, value):
        if isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        else:
            return 0


class RedisInt(int, RedisType):
    serializer = IntegerSerializer(int, None)

    def __new__(cls, value=0, **kwargs):
        if value is None:
            value = 0
        return super().__new__(cls, value)

    def __init__(self, value=0, **kwargs):
        RedisType.__init__(self, **kwargs)

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        if redis_value is not None:
            return self.serializer.deserialize_value(redis_value)
        return 0

    async def set(self, value: int):
        if not isinstance(value, int):
            raise TypeError("Value must be int")

        serialized_value = self.serializer.serialize_value(value)
        return await self.client.json().set(
            self.redis_key, self.json_path, serialized_value
        )

    async def increase(self, amount: int = 1):
        result = await self.client.json().numincrby(
            self.redis_key, self.json_path, amount
        )
        return result[0] if isinstance(result, list) and result else result

    def clone(self):
        return int(self)
