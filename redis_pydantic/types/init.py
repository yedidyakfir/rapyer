from datetime import datetime
from enum import Enum
from typing import Any, get_origin

from pydantic import BaseModel

from redis_pydantic.types.any import AnyTypeRedis
from redis_pydantic.types.base import PydanicSerializer

# from redis_pydantic.types.enm import EnumSerializer
from redis_pydantic.types.lst import RedisList
from redis_pydantic.types.dct import RedisDict
from redis_pydantic.types.byte import RedisBytes
from redis_pydantic.types.integer import RedisInt
from redis_pydantic.types.boolean import RedisBool
from redis_pydantic.types.string import RedisStr
from redis_pydantic.types.datetime import RedisDatetime

from redis_pydantic.types.string import StringSerializer
from redis_pydantic.types.integer import IntegerSerializer
from redis_pydantic.types.boolean import BooleanSerializer
from redis_pydantic.types.byte import ByteSerializer
from redis_pydantic.types.any import AnySerializer
from redis_pydantic.types.lst import ListSerializer
from redis_pydantic.types.dct import DictSerializer
from redis_pydantic.types.datetime import DatetimeSerializer


ALL_TYPES = {
    list: RedisList,
    dict: RedisDict,
    bytes: RedisBytes,
    int: RedisInt,
    bool: RedisBool,
    str: RedisStr,
    datetime: RedisDatetime,
    Any: AnyTypeRedis,
}

SERIALIZER = {
    list: ListSerializer,
    dict: DictSerializer,
    bytes: ByteSerializer,
    int: IntegerSerializer,
    bool: BooleanSerializer,
    str: StringSerializer,
    datetime: DatetimeSerializer,
    Any: AnySerializer,
    # Enum: EnumSerializer,
}


def create_serializer(type_annotation):
    serializer_creator = create_serializer

    origin_type = get_origin(type_annotation) or type_annotation
    if issubclass(origin_type, BaseModel):
        return PydanicSerializer(type_annotation, serializer_creator)
    serializer_type = SERIALIZER.get(origin_type, AnySerializer)
    return serializer_type(type_annotation, serializer_creator)
