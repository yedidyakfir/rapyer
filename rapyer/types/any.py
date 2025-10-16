import copy
import pickle
import base64

from rapyer.types.base import RedisType, RedisSerializer


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

    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(value, AnyTypeRedis):
            value = value.value
        self.value = value

    async def load(self):
        redis_items = await self.client.json().get(self.redis_key, self.field_path)
        return self.serializer.deserialize_value(redis_items)

    def clone(self):
        return copy.copy(self.value)

    def serialize_value(self, value):
        # If the value passed is this redis object itself, use self.value instead
        if isinstance(value, AnyTypeRedis):
            value = value.value
        return self.serializer.serialize_value(value)

    def deserialize_value(self, value):
        if isinstance(value, AnyTypeRedis):
            value = value.value
        return self.serializer.deserialize_value(value)

    async def set(self, value):
        self.value = value
        serialized_value = self.serializer.serialize_value(value)
        return await self.client.json().set(
            self.redis_key, self.json_path, serialized_value
        )

    def __eq__(self, other):
        if isinstance(other, AnyTypeRedis):
            other = other.value
        return self.value == other
