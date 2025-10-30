from datetime import datetime

from rapyer.types.byte import RedisBytes
from rapyer.types.datetime import RedisDatetime
from rapyer.types.dct import RedisDict
from rapyer.types.integer import RedisInt
from rapyer.types.lst import RedisList
from rapyer.types.string import RedisStr

ALL_TYPES = {
    list: RedisList,
    dict: RedisDict,
    bytes: RedisBytes,
    int: RedisInt,
    str: RedisStr,
    datetime: RedisDatetime,
}
