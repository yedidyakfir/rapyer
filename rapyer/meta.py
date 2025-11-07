import base64
import functools
import pickle
from typing import Any

from pydantic import field_serializer, field_validator, TypeAdapter
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from pydantic_core.core_schema import FieldSerializationInfo, ValidationInfo

from rapyer.types.base import REDIS_DUMP_FLAG_NAME, RedisType
from rapyer.types.convert import RedisConverter
from rapyer.utils.annotation import replace_to_redis_types_in_annotation
from rapyer.utils.fields import (
    fields_from_base_cls,
    find_first_type_in_annotation,
    convert_field_factory_type,
)


def make_pickle_field_serializer(field: str):
    @field_serializer(field, when_used="json-unless-none")
    def pickle_field_serializer(v, info: FieldSerializationInfo):
        ctx = info.context or {}
        should_serialize_redis = ctx.get(REDIS_DUMP_FLAG_NAME, False)
        if should_serialize_redis:
            return base64.b64encode(pickle.dumps(v)).decode("utf-8")
        return v

    pickle_field_serializer.__name__ = f"__serialize_{field}"

    @field_validator(field, mode="before")
    def pickle_field_validator(v, info: ValidationInfo):
        if v is None:
            return v
        ctx = info.context or {}
        should_serialize_redis = ctx.get(REDIS_DUMP_FLAG_NAME, False)
        if should_serialize_redis:
            return pickle.loads(base64.b64decode(v))
        return v

    pickle_field_validator.__name__ = f"__deserialize_{field}"

    return pickle_field_serializer, pickle_field_validator


class RapyerMeta(ModelMetaclass):
    def __new__(
        mcs,
        cls_name: str,
        bases: tuple[type],
        namespace: dict[str, Any],
        **kwargs: dict,
    ):
        """
        We adjust the type and default values to be redis supported.
        The new types inherit from the old, so it would be seamless for the user
        but will allow the user to interact with redis actions
        """
        if cls_name == "AtomicRedisModel":
            return super().__new__(mcs, cls_name, bases, namespace, **kwargs)

        from rapyer.base import AtomicRedisModel

        annotations = namespace.get("__annotations__", {}).copy()
        first_base_atomic = next(
            cls for cls in bases if issubclass(cls, AtomicRedisModel)
        )
        meta_config = first_base_atomic.Meta

        # Redefine annotations to use redis types
        pydantic_annotation = fields_from_base_cls(bases, AtomicRedisModel)
        new_annotation = {
            field_name: field.annotation
            for field_name, field in pydantic_annotation.items()
        }
        original_annotations = annotations.copy()
        original_annotations.update(new_annotation)
        new_annotations = {
            field_name: replace_to_redis_types_in_annotation(
                annotation,
                RedisConverter(meta_config.redis_type, f".{field_name}"),
            )
            for field_name, annotation in original_annotations.items()
        }
        annotations.update(new_annotations)
        namespace["__annotations__"] = annotations

        for field_name, field in pydantic_annotation.items():
            if field_name not in namespace:
                namespace[field_name] = field

        # Set new default values if needed
        type_support_check = RedisConverter(meta_config.redis_type, "")
        for attr_name, attr_type in annotations.items():
            if not type_support_check.is_annotation_support(attr_type):
                serializer, validator = make_pickle_field_serializer(attr_name)
                namespace[serializer.__name__] = serializer
                namespace[validator.__name__] = validator
                continue
            value = namespace.get(attr_name)
            if value is None:
                continue

            real_type = find_first_type_in_annotation(attr_type)

            if isinstance(value, real_type):
                continue
            redis_type = annotations[attr_name]
            redis_type: type[RedisType]
            adapter = TypeAdapter(redis_type)

            # Handle Field(default=...)
            if isinstance(value, FieldInfo):
                if value.default != PydanticUndefined:
                    value.default = adapter.validate_python(value.default)
                elif value.default_factory != PydanticUndefined and callable(
                    value.default_factory
                ):
                    test_value = value.default_factory()
                    if isinstance(test_value, real_type):
                        continue
                    original_factory = value.default_factory
                    validate_from_adapter = functools.partial(
                        convert_field_factory_type, original_factory, adapter
                    )
                    value.default_factory = validate_from_adapter
            else:
                namespace[attr_name] = adapter.validate_python(value)

        cls = super().__new__(mcs, cls_name, bases, namespace, **kwargs)
        return cls
