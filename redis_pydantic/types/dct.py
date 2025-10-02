from redis_pydantic.types.base import RedisType


class RedisDict(dict, RedisType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def load(self):
        pass

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def update(self, *args, **kwargs):
        pass

    def pop(self, key, default=None):
        pass

    def popitem(self):
        pass

    def clear(self):
        pass
