from typing import TypeAlias, TYPE_CHECKING

from rapyer.types.base import RedisType


class RedisFloat(float, RedisType):
    original_type = float

    @classmethod
    def redis_schema(cls, field_name: str):
        from redis.commands.search.field import NumericField
        return NumericField(field_name)

    def clone(self):
        return float(self)

    def __iadd__(self, other):
        new_value = self + other
        if self.pipeline:
            self.pipeline.json().set(self.key, self.json_path, new_value)
        return self.__class__(new_value)

    def __isub__(self, other):
        new_value = self - other
        if self.pipeline:
            self.pipeline.json().set(self.key, self.json_path, new_value)
        return self.__class__(new_value)

    def __imul__(self, other):
        new_value = self * other
        if self.pipeline:
            self.pipeline.json().set(self.key, self.json_path, new_value)
        return self.__class__(new_value)

    def __itruediv__(self, other):
        new_value = self / other
        if self.pipeline:
            self.pipeline.json().set(self.key, self.json_path, new_value)
        return self.__class__(new_value)


if TYPE_CHECKING:
    RedisFloat: TypeAlias = RedisFloat | float