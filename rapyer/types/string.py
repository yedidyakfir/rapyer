from rapyer.types.base import RedisType, RedisSerializer


class StringSerializer(RedisSerializer):
    def serialize_value(self, value):
        return str(value) if value is not None else None

    def deserialize_value(self, value):
        if isinstance(value, str):
            return value
        elif isinstance(value, bytes):
            return value.decode()
        else:
            return str(value)


class RedisStr(str, RedisType):
    serializer = StringSerializer(str, None)

    def __new__(cls, value="", **kwargs):
        if value is None:
            value = ""
        return super().__new__(cls, value)

    def __init__(self, value="", **kwargs):
        RedisType.__init__(self, **kwargs)

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        if redis_value is not None:
            return self.serializer.deserialize_value(redis_value)
        return ""

    async def set(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Value must be str")

        serialized_value = self.serializer.serialize_value(value)
        return await self.client.json().set(
            self.redis_key, self.json_path, serialized_value
        )

    def clone(self):
        return str(self)
