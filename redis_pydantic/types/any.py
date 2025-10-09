import copy
import pickle
import base64

from redis_pydantic.types.base import RedisType, RedisSerializer


class AnySerializer(RedisSerializer):
    def serialize_value(self, value):
        pickled_data = pickle.dumps(value)
        return base64.b64encode(pickled_data).decode()

    def deserialize_value(self, value):
        if value is None:
            return None
        pickled_data = base64.b64decode(value)
        return pickle.loads(pickled_data)


class AnyTypeRedis(RedisType):
    serializer = AnySerializer(object, None)

    async def load(self):
        redis_items = await self.client.json().get(self.redis_key, self.field_path)
        return self.serializer.deserialize_value(redis_items)

    def clone(self):
        return copy.copy(self)

    async def set(self, value):
        serialized_value = self.serializer.serialize_value(value)
        return await self.client.json().set(
            self.redis_key, self.json_path, serialized_value
        )
