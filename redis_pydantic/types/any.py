import copy
import pickle

from redis_pydantic.types.base import RedisType


class AnyTypeRedis(RedisType):
    async def load(self):
        redis_items = await self.client.json().get(self.redis_key, self.field_path)
        return self.deserialize_value(redis_items)

    def clone(self):
        return copy.copy(self)

    def serialize_value(self, value):
        return pickle.dumps(value)

    def deserialize_value(self, value):
        return pickle.loads(value)
