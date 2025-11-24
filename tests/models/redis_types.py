from typing import Annotated

from pydantic import Field

from rapyer.base import AtomicRedisModel
from rapyer.types.byte import RedisBytesType
from rapyer.types.dct import RedisDict, RedisDictType
from rapyer.types.integer import RedisInt, RedisIntType
from rapyer.types.lst import RedisList, RedisListType
from rapyer.types.string import RedisStr, RedisStrType


# Models with direct Redis type annotations
class DirectRedisStringModel(AtomicRedisModel):
    name: RedisStrType = ""


class DirectRedisIntModel(AtomicRedisModel):
    count: RedisIntType = 0


class DirectRedisBytesModel(AtomicRedisModel):
    data: RedisBytesType = b""


class DirectRedisListModel(AtomicRedisModel):
    items: RedisListType[str] = Field(default_factory=list)


class DirectRedisListIntModel(AtomicRedisModel):
    numbers: RedisListType[int] = Field(default_factory=list)


class DirectRedisDictModel(AtomicRedisModel):
    metadata: RedisDictType[str] = Field(default_factory=dict)


class DirectRedisDictIntModel(AtomicRedisModel):
    counters: RedisDict[int] = Field(default_factory=dict)


class MixedDirectRedisTypesModel(AtomicRedisModel):
    name: RedisStr = "default"
    count: RedisInt = 0
    active: bool = True
    tags: RedisList[str] = Field(default_factory=list)
    config: RedisDict[int] = Field(default_factory=dict)


class AnnotatedDirectRedisTypesModel(AtomicRedisModel):
    title: Annotated[RedisStr, Field(description="Title field")] = "default_title"
    score: Annotated[RedisInt, Field(ge=0, description="Score field")] = 0
    enabled: Annotated[bool, Field(description="Enabled flag")] = False
    categories: Annotated[RedisList[str], Field(description="Categories list")] = Field(
        default_factory=list
    )
    settings: Annotated[RedisDict[str], Field(description="Settings dict")] = Field(
        default_factory=dict
    )
