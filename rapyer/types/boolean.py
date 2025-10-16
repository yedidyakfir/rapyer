from rapyer.types.base import RedisType, RedisSerializer


class BooleanSerializer(RedisSerializer):
    def serialize_value(self, value):
        return bool(value) if value is not None else False

    def deserialize_value(self, value):
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return bool(value)
        elif isinstance(value, str):
            return value.lower() in ("true", "1")
        else:
            return bool(value)


class RedisBool(int, RedisType):
    serializer = BooleanSerializer(bool, None)

    def __new__(cls, value=False, **kwargs):
        if value is None:
            value = False
        return super().__new__(cls, bool(value))

    def __init__(self, value=False, **kwargs):
        RedisType.__init__(self, **kwargs)

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        if redis_value is not None:
            return self.serializer.deserialize_value(redis_value)
        return False

    async def set(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("Value must be bool")

        serialized_value = self.serializer.serialize_value(value)
        return await self.client.json().set(
            self.redis_key, self.json_path, serialized_value
        )

    def clone(self):
        return bool(self)
