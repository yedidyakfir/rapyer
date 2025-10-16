class RedisPydanticError(Exception):
    """Base exception for all redis-pydantic errors."""

    pass


class KeyNotFound(RedisPydanticError):
    """Raised when a key is not found in Redis."""

    pass
