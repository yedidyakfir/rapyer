from typing import TypeAlias

from rapyer.types.base import RedisType


class RedisInt(int, RedisType):
    original_type = int

    async def increase(self, amount: int = 1):
        result = await self.client.json().numincrby(self.key, self.json_path, amount)
        return result[0] if isinstance(result, list) and result else result

    def clone(self):
        return int(self)

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

    def __ifloordiv__(self, other):
        new_value = self // other
        if self.pipeline:
            self.pipeline.json().set(self.key, self.json_path, new_value)
        return self.__class__(new_value)

    def __imod__(self, other):
        new_value = self % other
        if self.pipeline:
            self.pipeline.json().set(self.key, self.json_path, new_value)
        return self.__class__(new_value)

    def __ipow__(self, other):
        new_value = self**other
        if self.pipeline:
            self.pipeline.json().set(self.key, self.json_path, new_value)
        return self.__class__(new_value)


RedisIntType: TypeAlias = RedisInt | int
