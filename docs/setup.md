# Setup Guide

This guide will help you install and configure Rapyer in your project.

## Installation

### Requirements

- **Python 3.10+** - Rapyer requires modern Python features
- **Redis server with JSON module** - For data storage
- **Pydantic v2** - For type validation (installed automatically)

### Install Rapyer

```bash
pip install rapyer
```

### Redis Setup

Rapyer requires Redis with the JSON module enabled. Here are several options:

#### Option 1: Redis Stack (Recommended)
Redis Stack includes the JSON module by default:

##### Using Docker
```bash
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack-server:latest
```

##### Ubuntu/Debian
```bash
sudo apt install redis-stack-server
```

##### macOS
```bash
brew install redis-stack
```

#### Option 2: Redis with RedisJSON Module
If you have an existing Redis installation:

```bash
# Install RedisJSON module
# Method varies by installation - check RedisJSON documentation
```

#### Option 3: Cloud Redis
Use managed Redis services that support modules:
- Redis Cloud
- AWS ElastiCache (with RedisJSON)
- Google Cloud Memorystore

## Configuration

> **⚠️ IMPORTANT**: When creating your Redis client, always use `decode_responses=True` to prevent typing errors and ensure proper string handling. This is crucial for Rapyer to work correctly with string-based operations.

### Basic Configuration

Set up your Redis connection in your application:

```python
import redis.asyncio as redis
from rapyer import AtomicRedisModel

# Configure Redis connection
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True  # IMPORTANT: Set to True to prevent typing errors
)

# Set the global Redis client for your models
class User(AtomicRedisModel):
    name: str
    age: int
    
    class Meta:
        redis = redis_client
```

### Using Redis URL

For production environments, use connection URLs:

```python
import redis.asyncio as redis
from rapyer import AtomicRedisModel

# From URL (supports redis://, rediss://, unix://)
redis_client = redis.from_url(
    "redis://localhost:6379/0",
    decode_responses=True  # IMPORTANT: Set to True to prevent typing errors
)

class User(AtomicRedisModel):
    name: str
    
    class Meta:
        redis = redis_client  # This is the default option with no user initialization
```

### Environment Variables

For different environments, use environment variables:

```python
import os
import redis.asyncio as redis
from rapyer import AtomicRedisModel

redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True  # IMPORTANT: Set to True to prevent typing errors
)

class User(AtomicRedisModel):
    name: str
    
    class Meta:
        redis = redis_client
```

### Advanced Configuration

#### Connection Pooling

```python
import redis.asyncio as redis
from rapyer import AtomicRedisModel

# Custom connection pool
pool = redis.ConnectionPool.from_url(
    "redis://localhost:6379/0",
    max_connections=20,
    decode_responses=True  # IMPORTANT: Set to True to prevent typing errors
)

redis_client = redis.Redis(connection_pool=pool)

class User(AtomicRedisModel):
    name: str
    
    class Meta:
        redis = redis_client
```

#### TTL (Time To Live)

Set automatic expiration for your models:

```python
from rapyer import AtomicRedisModel

class Session(AtomicRedisModel):
    user_id: str
    data: dict = {}
    
    class Meta:
        redis = redis_client
        ttl = 3600  # Expire after 1 hour
```

## Verification

Test your setup with this simple script:

```python
import asyncio
import redis.asyncio as redis
from rapyer import AtomicRedisModel

# Setup Redis client
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True  # IMPORTANT: Set to True to prevent typing errors
)

class TestModel(AtomicRedisModel):
    message: str
    
    class Meta:
        redis = redis_client

async def test_setup():
    try:
        # Test basic operations
        model = TestModel(message="Hello, Rapyer!")
        await model.save()
        
        # Retrieve the model
        retrieved = await TestModel.get(model.key)
        print(f"Success! Retrieved: {retrieved.message}")
        
        # Cleanup
        await model.delete()
        print("Setup verification complete!")
        
    except Exception as e:
        print(f"Setup error: {e}")
    finally:
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(test_setup())
```

If this script runs without errors and prints "Success!", your setup is complete!

## Troubleshooting

### Common Issues

#### "RedisJSON module not loaded"
**Solution**: Ensure you're using Redis Stack or have the RedisJSON module installed.

#### "decode_responses must be True"
**Solution**: Set `decode_responses=True` in your Redis client configuration to prevent typing errors.

#### "Connection refused"
**Solution**: Ensure Redis server is running and accessible at the specified host/port.

#### Import errors
**Solution**: Ensure you have Python 3.10+ and all dependencies are installed.

### Docker Compose Example

For development, use this Docker Compose setup:

```yaml
version: '3.8'
services:
  redis:
    image: redis/redis-stack-server:latest
    ports:
      - "6379:6379"
    environment:
      - REDIS_ARGS=--save 60 1000
```

## Next Steps

Now that Rapyer is set up, learn about:

- **[Basic Operations](basic-operations.md)** - Save, load, get, and delete operations
- **[Supported Types](supported-types.md)** - All supported data types and their atomic operations
- **[Atomic Actions](atomic-actions.md)** - Advanced concurrency features