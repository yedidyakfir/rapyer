from datetime import datetime
from enum import Enum
from typing import Any, get_origin

from pydantic import BaseModel

from rapyer.types.any import AnyTypeRedis
from rapyer.types.base import PydanicSerializer

# from redis_pydantic.types.enm import EnumSerializer
from rapyer.types.lst import RedisList
from rapyer.types.dct import RedisDict
from rapyer.types.byte import RedisBytes
from rapyer.types.integer import RedisInt
from rapyer.types.boolean import RedisBool
from rapyer.types.string import RedisStr
from rapyer.types.datetime import RedisDatetime

from rapyer.types.string import StringSerializer
from rapyer.types.integer import IntegerSerializer
from rapyer.types.boolean import BooleanSerializer
from rapyer.types.byte import ByteSerializer
from rapyer.types.any import AnySerializer
from rapyer.types.lst import ListSerializer
from rapyer.types.dct import DictSerializer
from rapyer.types.datetime import DatetimeSerializer


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
