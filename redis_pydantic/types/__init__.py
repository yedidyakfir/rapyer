from typing import Any

from redis_pydantic.types.any import AnyTypeRedis
from redis_pydantic.types.lst import RedisList
from redis_pydantic.types.dct import RedisDict
from redis_pydantic.types.byte import RedisBytes
from redis_pydantic.types.integer import RedisInt
from redis_pydantic.types.boolean import RedisBool
from redis_pydantic.types.string import RedisStr

ALL_TYPES = {
    list: RedisList,
    dict: RedisDict,
    bytes: RedisBytes,
    int: RedisInt,
    bool: RedisBool,
    str: RedisStr,
    Any: AnyTypeRedis,
}
