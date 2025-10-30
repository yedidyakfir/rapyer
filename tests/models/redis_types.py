from typing import Annotated
from pydantic import Field

from rapyer.base import AtomicRedisModel
from rapyer.types.boolean import RedisBool
from rapyer.types.byte import RedisBytes
from rapyer.types.dct import RedisDict
from rapyer.types.integer import RedisInt
from rapyer.types.lst import RedisList
from rapyer.types.string import RedisStr


# Models with direct Redis type annotations
class DirectRedisStringModel(AtomicRedisModel):
    name: RedisStr = RedisStr("")


class DirectRedisIntModel(AtomicRedisModel):
    count: RedisInt = RedisInt(0)


class DirectRedisBoolModel(AtomicRedisModel):
    flag: RedisBool = RedisBool(False)


class DirectRedisBytesModel(AtomicRedisModel):
    data: RedisBytes = RedisBytes(b"")


class DirectRedisListModel(AtomicRedisModel):
    items: RedisList[str] = Field(default_factory=list)


class DirectRedisListIntModel(AtomicRedisModel):
    numbers: RedisList[int] = Field(default_factory=list)


class DirectRedisDictModel(AtomicRedisModel):
    metadata: RedisDict[str, str] = Field(default_factory=dict)


class DirectRedisDictIntModel(AtomicRedisModel):
    counters: RedisDict[str, int] = Field(default_factory=dict)


class MixedDirectRedisTypesModel(AtomicRedisModel):
    name: RedisStr = RedisStr("default")
    count: RedisInt = RedisInt(0)
    active: RedisBool = RedisBool(True)
    tags: RedisList[str] = Field(default_factory=list)
    config: RedisDict[str, int] = Field(default_factory=dict)


class AnnotatedDirectRedisTypesModel(AtomicRedisModel):
    title: Annotated[RedisStr, Field(description="Title field")] = RedisStr("default_title")
    score: Annotated[RedisInt, Field(ge=0, description="Score field")] = RedisInt(0)
    enabled: Annotated[RedisBool, Field(description="Enabled flag")] = RedisBool(False)
    categories: Annotated[RedisList[str], Field(description="Categories list")] = Field(
        default_factory=list
    )
    settings: Annotated[RedisDict[str, str], Field(description="Settings dict")] = Field(
        default_factory=dict
    )