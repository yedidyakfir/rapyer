from redis_pydantic.types.base import RedisType
from redis_pydantic.context import _context_var


class RedisList(list, RedisType):
    def __init__(self, *args, redis_key: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_key = redis_key

    def load(self):
        pass

    def append(self, __object):
        redis = _context_var.get()
        redis.rpush(self.redis_key, __object)

    def extend(self, __iterable):
        pass

    def pop(self, *args, **kwargs):
        pass

    def remove(self, __value):
        pass

    def reverse(self, *args, **kwargs):
        pass

    def sort(self, *args, **kwargs):
        pass
