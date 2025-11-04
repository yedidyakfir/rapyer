from typing import Type, Any
from pydantic import ConfigDict, Field

from rapyer.base import AtomicRedisModel


class ModelWithUnserializableFields(AtomicRedisModel):
    # name: str
    model_type: Type = Field(default=str)
    # callable_field: type = Field(default=type)
    # python_type: Type[Any] = Field(default=Any)
    # value: int = Field(default=42)
