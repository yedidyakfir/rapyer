# Configuration

## Redis Connection Setup

### Default Connection

By default, RedisPydantic connects to `redis://localhost:6379/0`.

### Custom Connection

Configure Redis connection in your model's `Meta` class:

```python
import redis.asyncio as redis
from redis_pydantic.base import BaseRedisModel

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.from_url("redis://your-redis-host:6379/1")
```

### Environment-based Configuration

```python
import os
import redis.asyncio as redis
from redis_pydantic.base import BaseRedisModel

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.from_url(redis_url)
```

### Connection with Authentication

```python
import redis.asyncio as redis
from redis_pydantic.base import BaseRedisModel

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.from_url(
            "redis://username:password@your-redis-host:6379/0",
            decode_responses=True
        )
```

### Connection Pooling

For high-concurrency applications, configure connection pooling:

```python
import redis.asyncio as redis
from redis_pydantic.base import BaseRedisModel

# Create connection pool
pool = redis.ConnectionPool.from_url(
    "redis://localhost:6379/0",
    max_connections=20
)

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.Redis(connection_pool=pool)
```

### SSL/TLS Configuration

For secure connections:

```python
import redis.asyncio as redis
from redis_pydantic.base import BaseRedisModel

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.from_url(
            "rediss://your-redis-host:6380/0",  # Note the 'rediss://' for SSL
            ssl_cert_reqs=None,
            ssl_ca_certs=None,
            ssl_certfile=None,
            ssl_keyfile=None
        )
```

## Model Configuration

### Custom Key Prefix

By default, keys use the model class name. You can customize this:

```python
class User(BaseRedisModel):
    name: str
    
    class Meta:
        key_prefix = "user"  # Instead of "User"
```

### Model Validation

Configure Pydantic validation:

```python
from pydantic import ConfigDict

class User(BaseRedisModel):
    name: str
    age: int
    
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        validate_default=True
    )
```

## Performance Tuning

### Connection Pool Settings

```python
pool = redis.ConnectionPool.from_url(
    "redis://localhost:6379/0",
    max_connections=20,      # Max connections in pool
    retry_on_timeout=True,   # Retry on timeout
    socket_keepalive=True,   # Keep TCP connections alive
    socket_keepalive_options={},
    health_check_interval=30  # Health check every 30 seconds
)
```

### Batch Operations

Use pipeline context for multiple operations:

```python
async with user.pipeline() as pipelined_user:
    await pipelined_user.tags.aappend("tag1")
    await pipelined_user.tags.aappend("tag2")
    await pipelined_user.metadata.aset_item("key", "value")
    # All operations executed atomically
```

## Error Handling

Configure retry and timeout settings:

```python
import redis.asyncio as redis
from redis_pydantic.base import BaseRedisModel

class MyModel(BaseRedisModel):
    name: str
    
    class Meta:
        redis = redis.from_url(
            "redis://localhost:6379/0",
            socket_timeout=5,        # 5 second socket timeout
            socket_connect_timeout=5, # 5 second connection timeout
            retry_on_timeout=True,   # Retry on timeout
            health_check_interval=30  # Health check interval
        )
```