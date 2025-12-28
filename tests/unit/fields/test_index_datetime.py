from datetime import datetime
from typing import get_args

from rapyer.fields import Index
from rapyer.types.datetime import RedisDatetimeTimestamp


def test_index_datetime_uses_timestamp_type_sanity():
    # Arrange & Act
    indexed_datetime = Index[datetime]

    # Assert
    args = get_args(indexed_datetime)
    assert args, "Index[datetime] should have type arguments"
    actual_type = args[0]
    assert (
        actual_type is RedisDatetimeTimestamp
    ), f"Expected RedisDatetimeTimestamp, got {actual_type}"


def test_index_datetime_uses_timestamp_type_with_call_sanity():
    # Arrange & Act
    indexed_datetime = Index(datetime)

    # Assert
    args = get_args(indexed_datetime)
    assert args, "Index[datetime] should have type arguments"
    actual_type = args[0]
    assert (
        actual_type is RedisDatetimeTimestamp
    ), f"Expected RedisDatetimeTimestamp, got {actual_type}"
