from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, BaseModel

from rapyer import AtomicRedisModel


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class StrDictModel(AtomicRedisModel):
    metadata: dict[str, str] = Field(default_factory=dict)


class IntDictModel(AtomicRedisModel):
    metadata: dict[str, int] = Field(default_factory=dict)


class BytesDictModel(AtomicRedisModel):
    metadata: dict[str, bytes] = Field(default_factory=dict)


class DatetimeDictModel(AtomicRedisModel):
    metadata: dict[str, datetime] = Field(default_factory=dict)


class EnumDictModel(AtomicRedisModel):
    metadata: dict[str, Status] = Field(default_factory=dict)


class AnyDictModel(AtomicRedisModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


# Additional complex types
class Person(BaseModel):
    name: str
    age: int
    email: str


class Company(BaseModel):
    name: str
    employees: int
    founded: int


class BaseModelDictModel(AtomicRedisModel):
    metadata: dict[str, Person] = Field(default_factory=dict)


class BoolDictModel(AtomicRedisModel):
    metadata: dict[str, bool] = Field(default_factory=dict)


class ListDictModel(AtomicRedisModel):
    metadata: dict[str, list[str]] = Field(default_factory=dict)


class NestedDictModel(AtomicRedisModel):
    metadata: dict[str, dict[str, str]] = Field(default_factory=dict)
