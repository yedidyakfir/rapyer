from redis_pydantic.types.base import RedisType


class RedisDict(dict, RedisType):
    def __init__(self, *args, **kwargs):
        RedisType.__init__(self, **kwargs)
        super().__init__(*args)

    async def load(self):
        # Get all items from Redis dict
        redis_items = await self.pipeline.json().get(self.redis_key, self.field_path)

        if redis_items is None:
            redis_items = {}

        # Clear local dict and populate with Redis data
        super().clear()
        super().update(redis_items)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)

        return self.pipeline.json().set(
            self.redis_key, f"{self.json_path}.{key}", str(value)
        )

    def __delitem__(self, key):
        super().__delitem__(key)

        return self.pipeline.json().delete(self.redis_key, f"{self.json_path}.{key}")

    def update(self, **kwargs):
        super().update(kwargs)
        redis_kwargs = {f"{self.json_path}.{k}": v for k, v in kwargs.items()}
        return self.pipeline.json().mset(
            [
                (self.redis_key, field_name, value)
                for field_name, value in redis_kwargs.items()
            ]
        )

    def pop(self, key, default=None):
        if key in self:
            value = super().pop(key)
            self.pipeline.json().delete(self.redis_key, f"{self.json_path}.{key}")
            return value
        elif default is not None:
            return default
        else:
            raise KeyError(key)

    def popitem(self):
        key, value = super().popitem()
        self.pipeline.json().delete(self.redis_key, f"{self.json_path}.{key}")
        return key, value

    def clear(self):
        # Clear local dict
        super().clear()

        # Clear Redis dict
        return self.pipeline.json().delete(self.redis_key, self.json_path)

    def clone(self):
        return dict.copy(self)
