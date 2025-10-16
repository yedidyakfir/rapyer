import base64
from rapyer.types.base import RedisType, RedisSerializer


class ByteSerializer(RedisSerializer):
    def serialize_value(self, value):
        if isinstance(value, bytes):
            return base64.b64encode(value).decode()
        elif isinstance(value, str):
            return base64.b64encode(value.encode()).decode()
        else:
            return base64.b64encode(str(value).encode()).decode()

    def deserialize_value(self, value):
        if isinstance(value, str):
            try:
                return base64.b64decode(value)
            except Exception:
                return value.encode()
        elif isinstance(value, bytes):
            return value
        else:
            return str(value).encode()


class RedisBytes(bytes, RedisType):
    serializer = ByteSerializer(bytes, None)

    def __new__(cls, value=b"", **kwargs):
        if value is None:
            value = b""
        return super().__new__(cls, value)

    def __init__(self, value=b"", **kwargs):
        RedisType.__init__(self, **kwargs)

    async def load(self):
        redis_value = await self.client.json().get(self.redis_key, self.field_path)
        if redis_value is not None:
            return self.serializer.deserialize_value(redis_value)
        return b""

    async def set(self, value: bytes):
        if not isinstance(value, bytes):
            raise TypeError("Value must be bytes")

        serialized_value = self.serializer.serialize_value(value)
        return await self.client.json().set(
            self.redis_key, self.json_path, serialized_value
        )

    def clone(self):
        return bytes(self)
