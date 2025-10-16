# API Reference

Complete API reference for Rapyer.

## BaseRedisModel

The main class that provides Redis-backed Pydantic models.

### Class Methods

#### `get(key: str) -> BaseRedisModel`
Load a model instance by its Redis key.

```python
user = await User.get("User:123e4567-e89b-12d3-a456-426614174000")
```

#### `try_delete(key: str) -> bool`
Attempt to delete a model by key without loading it.

```python
deleted = await User.try_delete("User:123e4567-e89b-12d3-a456-426614174000")
```

### Instance Methods

#### `save() -> None`
Save the model to Redis.

```python
user = User(name="John", age=30)
await user.save()
```

#### `load() -> None`
Load all fields from Redis.

```python
await user.load()
```

#### `delete() -> None`
Delete the model from Redis.

```python
await user.delete()
```

#### `duplicate() -> BaseRedisModel`
Create a duplicate of the model with a new unique key.

```python
duplicate_user = await original_user.duplicate()
```

#### `duplicate_many(count: int) -> List[BaseRedisModel]`
Create multiple duplicates efficiently.

```python
duplicates = await original_user.duplicate_many(5)
```

#### `redis_dump() -> Dict[str, Any]`
Get the model as a Redis-compatible dictionary.

```python
data = user.redis_dump()
```

### Context Managers

#### `lock(action: str = "default") -> AsyncContextManager[BaseRedisModel]`
Create a distributed lock for atomic operations.

```python
async with user.lock("transfer") as locked_user:
    locked_user.balance -= 50
    locked_user.transaction_count += 1
    # Changes saved automatically on exit
```

#### `pipeline() -> AsyncContextManager[BaseRedisModel]`
Create a Redis pipeline for batched operations.

```python
async with user.pipeline() as pipelined_user:
    await pipelined_user.tags.aappend("tag1")
    await pipelined_user.metadata.aset_item("key", "value")
    # All operations executed atomically on exit
```

### TTL Methods

#### `set_ttl(seconds: int) -> None`
Set expiration time in seconds.

```python
await user.set_ttl(3600)  # Expires in 1 hour
```

#### `get_ttl() -> int`
Get remaining TTL in seconds.

```python
ttl = await user.get_ttl()
```

#### `remove_ttl() -> None`
Remove expiration (make persistent).

```python
await user.remove_ttl()
```

### Properties

#### `key: str`
The Redis key for this model instance.

```python
print(user.key)  # "User:123e4567-e89b-12d3-a456-426614174000"
```

#### `pk: str`
The primary key (UUID) for this model instance.

```python
print(user.pk)  # "123e4567-e89b-12d3-a456-426614174000"
```

## Redis Field Types

### RedisStr

String field with Redis operations.

#### Methods

##### `set(value: str) -> None`
Set the string value.

```python
await user.name.set("John Doe")
```

##### `load() -> None`
Load the value from Redis.

```python
await user.name.load()
```

### RedisInt

Integer field with Redis operations.

#### Methods

##### `set(value: int) -> None`
Set the integer value.

```python
await user.age.set(30)
```

##### `load() -> None`
Load the value from Redis.

```python
await user.age.load()
```

### RedisBool

Boolean field with Redis operations.

#### Methods

##### `set(value: bool) -> None`
Set the boolean value.

```python
await user.is_active.set(True)
```

##### `load() -> None`
Load the value from Redis.

```python
await user.is_active.load()
```

### RedisBytes

Bytes field with Redis operations (automatically base64 encoded).

#### Methods

##### `set(value: bytes) -> None`
Set the bytes value.

```python
await user.data.set(b"binary_data")
```

##### `load() -> None`
Load the value from Redis.

```python
await user.data.load()
```

### RedisList

List field with Redis operations.

#### Methods

##### `aappend(item: T) -> None`
Append a single item to the list.

```python
await user.tags.aappend("python")
```

##### `aextend(items: List[T]) -> None`
Extend the list with multiple items.

```python
await user.tags.aextend(["redis", "pydantic"])
```

##### `ainsert(index: int, item: T) -> None`
Insert an item at the specified index.

```python
await user.tags.ainsert(0, "first-tag")
```

##### `apop(index: int = -1) -> T`
Remove and return an item at the specified index (default: last item).

```python
last_item = await user.tags.apop()
first_item = await user.tags.apop(0)
```

##### `aclear() -> None`
Remove all items from the list.

```python
await user.tags.aclear()
```

##### `load() -> None`
Load the list from Redis.

```python
await user.tags.load()
```

### RedisDict

Dictionary field with Redis operations.

#### Methods

##### `aset_item(key: str, value: V) -> None`
Set a single key-value pair.

```python
await user.metadata.aset_item("role", "developer")
```

##### `aupdate(**kwargs) -> None`
Update multiple key-value pairs.

```python
await user.metadata.aupdate(role="developer", department="engineering")
```

##### `adel_item(key: str) -> None`
Delete a key from the dictionary.

```python
await user.metadata.adel_item("old_key")
```

##### `apop(key: str, default: V = None) -> V`
Remove and return a value by key, optionally with a default.

```python
value = await user.metadata.apop("role")
value = await user.metadata.apop("role", "unknown")
```

##### `apopitem() -> Tuple[str, V]`
Remove and return an arbitrary key-value pair.

```python
key, value = await user.metadata.apopitem()
```

##### `aclear() -> None`
Remove all items from the dictionary.

```python
await user.metadata.aclear()
```

##### `load() -> None`
Load the dictionary from Redis.

```python
await user.metadata.load()
```

## Configuration

### Meta Class

Configure Redis connection and model behavior.

```python
import redis.asyncio as redis

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.from_url("redis://localhost:6379/0")
        key_prefix = "custom_prefix"  # Optional custom key prefix
```

### Redis Connection Options

#### `redis.from_url(url, **kwargs)`
Create Redis connection from URL.

```python
redis_client = redis.from_url(
    "redis://localhost:6379/0",
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    max_connections=20
)
```

#### Common Connection Parameters

- `url`: Redis connection URL
- `decode_responses`: Whether to decode responses to strings
- `socket_timeout`: Socket timeout in seconds
- `socket_connect_timeout`: Connection timeout in seconds
- `retry_on_timeout`: Whether to retry on timeout
- `max_connections`: Maximum connections in pool
- `health_check_interval`: Health check interval in seconds

### SSL/TLS Configuration

```python
redis_client = redis.from_url(
    "rediss://localhost:6380/0",  # Note 'rediss://' for SSL
    ssl_cert_reqs=None,
    ssl_ca_certs=None,
    ssl_certfile=None,
    ssl_keyfile=None
)
```

## Exceptions

### Redis Exceptions

Rapyer uses the standard redis-py exceptions:

- `redis.exceptions.ConnectionError`: Connection failed
- `redis.exceptions.TimeoutError`: Operation timed out
- `redis.exceptions.AuthenticationError`: Authentication failed
- `redis.exceptions.ResponseError`: Redis server error

### Python Exceptions

- `TypeError`: Invalid type for field operation
- `KeyError`: Key not found in dictionary operations
- `IndexError`: Index out of range in list operations
- `ValueError`: Invalid value for field
- `RuntimeError`: Operation not allowed (e.g., duplicating inner models)

## Type Hints

Rapyer is fully typed. Common type annotations:

```python
from typing import List, Dict, Optional, Any
from rapyer.base import BaseRedisModel


class TypedModel(BaseRedisModel):
    name: str
    age: Optional[int] = None
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    data: Dict[str, Any] = {}
    scores: List[int] = []
    settings: Dict[str, bool] = {}
```

## Async Context Manager Protocol

Both `lock()` and `pipeline()` follow the async context manager protocol:

```python
class AsyncContextManager:
    async def __aenter__(self) -> BaseRedisModel:
        # Setup and return model instance
        ...
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # Cleanup and finalize operations
        ...
```

## Performance Considerations

### Operation Complexity

- **Primitive operations** (set, load): O(1)
- **List operations**: 
  - append/extend: O(N) where N is number of items
  - insert: O(N) where N is list length
  - pop: O(1) for last item, O(N) for other positions
- **Dict operations**: O(1) for single operations, O(N) for batch updates
- **Model save/load**: O(F) where F is number of fields

### Memory Usage

- Primitive fields: Minimal memory overhead
- Collections: Memory proportional to collection size
- Nested models: Additional overhead for Redis field wrapping

### Network Optimization

- Use batch operations (`aextend`, `aupdate`) when possible
- Use pipelines for multiple operations
- Load only required fields instead of entire models
- Configure connection pooling for high-concurrency applications