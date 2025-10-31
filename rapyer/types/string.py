from rapyer.types.base import RedisType


class RedisStr(str, RedisType):
    original_type = str

    def clone(self):
        return str(self)
