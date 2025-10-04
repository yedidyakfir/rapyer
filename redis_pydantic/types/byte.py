import base64
from redis_pydantic.types.base import RedisType


class RedisBytes(bytes, RedisType):
    def __init__(self, *args, **kwargs):
        RedisType.__init__(self, **kwargs)
        super().__init__(*args)

    async def load(self):
        redis_value = await self.pipeline.json().get(self.redis_key, self.field_path)
        if redis_value is not None:
            if isinstance(redis_value, str):
                try:
                    return base64.b64decode(redis_value)
                except Exception:
                    return redis_value.encode()
            elif isinstance(redis_value, bytes):
                return redis_value
            else:
                return str(redis_value).encode()
        return b""

    async def set(self, value: bytes):
        if not isinstance(value, bytes):
            raise TypeError("Value must be bytes")
        
        encoded_value = base64.b64encode(value).decode()
        return await self.pipeline.json().set(
            self.redis_key, self.json_path, encoded_value
        )

    def clone(self):
        return bytes(self)