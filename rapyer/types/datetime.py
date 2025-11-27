from datetime import datetime
from typing import TYPE_CHECKING

from rapyer.types.base import RedisType


class RedisDatetime(datetime, RedisType):
    original_type = datetime

    def __new__(cls, value, *args, **kwargs):
        if isinstance(value, datetime):
            # Support init from a datetime, preserving microseconds and timezone
            return datetime.__new__(
                cls,
                value.year,
                value.month,
                value.day,
                value.hour,
                value.minute,
                value.second,
                value.microsecond,
                value.tzinfo,
            )
        else:
            return datetime.__new__(cls, value, *args, **kwargs)

    def clone(self):
        return datetime.fromtimestamp(self.timestamp())


if TYPE_CHECKING:
    RedisDatetime = RedisDatetime | datetime
