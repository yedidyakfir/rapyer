from typing import Type, Any, Optional

from pydantic import Field

from rapyer.base import AtomicRedisModel


class ModelWithUnserializableFields(AtomicRedisModel):
    model_type: Optional[Type[str]] = Field(default=str)
    callable_field: Optional[type] = Field(default=type)
    python_type: Optional[Type[Any]] = Field(default=Any)
    value: Optional[int] = Field(default=42)
