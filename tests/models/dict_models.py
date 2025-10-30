from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, BaseModel

from rapyer import AtomicRedisModel


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


# Additional complex types
class Person(BaseModel):
    name: str
    age: int
    email: str


class Company(BaseModel):
    name: str
    employees: int
    founded: int


class BaseDictMetadataModel(AtomicRedisModel):
    metadata: dict


class StrDictModel(BaseDictMetadataModel):
    metadata: dict[str, str] = Field(default_factory=dict)


class IntDictModel(BaseDictMetadataModel):
    metadata: dict[str, int] = Field(default_factory=dict)


class BytesDictModel(BaseDictMetadataModel):
    metadata: dict[str, bytes] = Field(default_factory=dict)


class DatetimeDictModel(BaseDictMetadataModel):
    metadata: dict[str, datetime] = Field(default_factory=dict)


class EnumDictModel(BaseDictMetadataModel):
    metadata: dict[str, Status] = Field(default_factory=dict)


class AnyDictModel(BaseDictMetadataModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseModelDictModel(BaseDictMetadataModel):
    metadata: dict[str, Person] = Field(default_factory=dict)


class BoolDictModel(BaseDictMetadataModel):
    metadata: dict[str, bool] = Field(default_factory=dict)


class ListDictModel(BaseDictMetadataModel):
    metadata: dict[str, list[str]] = Field(default_factory=dict)


class NestedDictModel(BaseDictMetadataModel):
    metadata: dict[str, dict[str, str]] = Field(default_factory=dict)
