from redis.asyncio.client import Redis

from redis_pydantic.types.base import RedisType
from redis_pydantic.context import _context_var


class RedisList(list, RedisType):
    def __init__(self, *args, redis_key: str, field_path: str, redis: Redis, **kwargs):
        super(list, self).__init__(*args, **kwargs)
        self.redis_key = redis_key
        self.field_path = field_path
        self.redis = redis

    def load(self):
        pass

    def append(self, __object):
        redis = _context_var.get() or self.redis
        redis.json().arrappend(self.redis_key, self.field_path, __object)
        super(list, self).append(__object)

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
