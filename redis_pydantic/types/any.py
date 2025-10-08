import copy
import pickle
import base64

from redis_pydantic.types.base import RedisType


class AnyTypeRedis(RedisType):
    async def load(self):
        redis_items = await self.client.json().get(self.redis_key, self.field_path)
        return self.deserialize_value(redis_items)

    def clone(self):
        return copy.copy(self)

    def serialize_value(self, value):
        pickled_data = pickle.dumps(value)
        return base64.b64encode(pickled_data).decode()

    def deserialize_value(self, value):
        pickled_data = base64.b64decode(value)
        return pickle.loads(pickled_data)
