# Quick Start

This guide will get you up and running with RedisPydantic in minutes.

## Basic Model

Create your first Redis-backed Pydantic model:

```python
import asyncio
from redis_pydantic.base import BaseRedisModel
from typing import List, Dict

class User(BaseRedisModel):
    name: str
    age: int
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    score: int = 0
```

## Save and Load

```python
async def main():
    # Create a new user
    user = User(name="John", age=30)
    await user.save()
    
    # Load user by key
    loaded_user = await User.get(user.key)
    print(loaded_user.name)  # John
```

## Working with Fields

### String Fields

```python
# Set string value
await user.name.set("John Doe")

# Load from Redis
await user.name.load()
```

### List Fields

```python
# Add items to list
await user.tags.aappend("python")
await user.tags.aextend(["redis", "pydantic"])

# Pop items
popped = await user.tags.apop()  # Last item
popped = await user.tags.apop(0)  # First item
```

### Dictionary Fields

```python
# Set items
await user.metadata.aset_item("department", "engineering")
await user.metadata.aupdate(role="developer", level="senior")

# Get and remove items
value = await user.metadata.apop("role")
key, value = await user.metadata.apopitem()
```

## Running the Example

```python
import asyncio
from redis_pydantic.base import BaseRedisModel
from typing import List, Dict

class User(BaseRedisModel):
    name: str
    age: int
    tags: List[str] = []
    metadata: Dict[str, str] = {}
    score: int = 0

async def main():
    # Create and save user
    user = User(name="Alice", age=25)
    await user.save()
    
    # Add some data
    await user.tags.aextend(["python", "redis"])
    await user.metadata.aset_item("role", "developer")
    await user.score.set(100)
    
    # Load another instance
    user2 = await User.get(user.key)
    print(f"Name: {user2.name}")
    print(f"Tags: {user2.tags}")
    print(f"Metadata: {user2.metadata}")
    print(f"Score: {user2.score}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- Learn about [Configuration](configuration.md) options
- Explore [Supported Types](types.md)
- Check out [Advanced Features](advanced.md)