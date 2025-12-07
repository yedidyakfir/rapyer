# Installation

## Requirements

- **Python 3.10+** - Rapyer requires modern Python features
- **Redis server with JSON module** - For data storage
- **Pydantic v2** - For type validation (installed automatically)

## Install Rapyer

```bash
pip install rapyer
```

## Redis Setup

Rapyer requires Redis with the JSON module enabled. Here are several options:

### Option 1: Redis Stack (Recommended)
Redis Stack includes the JSON module by default:

#### Using Docker
```bash
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack-server:latest
```

#### Ubuntu/Debian
```bash
sudo apt install redis-stack-server
```

#### macOS
```bash
brew install redis-stack
```

### Option 2: Redis with RedisJSON Module
If you have an existing Redis installation, install the RedisJSON module according to the RedisJSON documentation.

### Option 3: Cloud Redis
Use managed Redis services that support modules:
- Redis Cloud
- AWS ElastiCache (with RedisJSON)
- Google Cloud Memorystore

## Basic Configuration

> **⚠️ IMPORTANT**: When creating your Redis client, always use `decode_responses=True` to prevent typing errors and ensure proper string handling.

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

# Define your model
class User(AtomicRedisModel):
    name: str
    age: int

# Set the Redis client for your model after class declaration
User.Meta.redis = redis_client
```

## Global Configuration with init_rapyer

For applications with multiple models, use `init_rapyer` to configure all models at once:

```python
import redis.asyncio as redis
from rapyer import AtomicRedisModel, init_rapyer

# Define your models first
class User(AtomicRedisModel):
    name: str
    age: int

class Session(AtomicRedisModel):
    user_id: str
    data: dict = {}

# Initialize all models with a Redis client
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# This will set a Redis client for ALL AtomicRedisModel classes
init_rapyer(redis=redis_client)

# Or use a Redis URL string
init_rapyer(redis="redis://localhost:6379/0")

# Or set both Redis client and TTL for all models
init_rapyer(redis=redis_client, ttl=3600)  # 1 hour TTL for all models
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
    decode_responses=True
)


class TestModel(AtomicRedisModel):
    message: str


# Set Redis client after class declaration
TestModel.Meta.redis = redis_client


async def test_setup():
    try:
        # Test basic operations
        model = TestModel(message="Hello, Rapyer!")
        await model.asave()

        # Retrieve the model
        retrieved = await TestModel.aget(model.key)
        print(f"Success! Retrieved: {retrieved.message}")

        # Cleanup
        await model.adelete()
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

**"RedisJSON module not loaded"**  
Ensure you're using Redis Stack or have the RedisJSON module installed.

**"decode_responses must be True"**  
Set `decode_responses=True` in your Redis client configuration to prevent typing errors.

**"Connection refused"**  
Ensure Redis server is running and accessible at the specified host/port.

**Import errors**  
Ensure you have Python 3.10+ and all dependencies are installed.

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