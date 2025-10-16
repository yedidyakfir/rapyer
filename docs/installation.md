# Installation

## Requirements

- Python 3.10+
- Redis server with JSON module
- Pydantic v2
- redis-py with async support

## Install from PyPI

```bash
pip install rapyer
```

## Redis Setup

Rapyer requires a Redis server with the JSON module enabled. You can either:

### Using Redis Stack

Install Redis Stack which includes the JSON module:

```bash
# Docker
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest

# Or using Redis Stack installer
# Visit: https://redis.io/download
```

### Using Redis with RedisJSON module

If you have an existing Redis installation, you can add the RedisJSON module:

```bash
# Load the module in redis.conf
loadmodule /path/to/redisjson.so

# Or load it at runtime
redis-cli MODULE LOAD /path/to/redisjson.so
```

## Verify Installation

Test your installation:

```python
import asyncio
from rapyer.base import BaseRedisModel


class TestModel(BaseRedisModel):
    name: str = "test"


async def test():
    model = TestModel()
    await model.save()
    print("Installation successful!")


asyncio.run(test())
```