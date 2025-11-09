# Overview

<div align="center">
  <img src="icon.png" alt="Rapyer Logo" width="120">
</div>

## Why Redis?

Redis is an in-memory key-value store designed for fast caching, queues, and real-time data processing. It offers high speed, atomic operations, and excellent scalability, making it ideal for low-latency applications. However, its main limitation is the cost of memory and limited persistence options compared to disk-based databases. Despite this, Redis remains a popular choice for performance-critical workloads.
## The Power of Pydantic

Pydantic has revolutionized Python data validation and serialization. There are already many libraries that use Pydantic for orm, Beanie(MongoDB), FastAPI(http server), etc, however the current packages to support redis are somewhat lacking.

Pydantic's strength lies in its automatic validation, type safety, and developer-friendly API that makes working with complex data structures intuitive and safe.

## Introducing Rapyer

Rapyer bridges the gap between Redis's performance and Pydantic's type safety, creating a powerful combination optimized for real-world applications.

### Wide Variety of Field Support

Rapyer supports a wide variety of field types and offers user to perform complex atomic actions of these fields.
- **Primitive types** - Optimized native Redis storage for strings, integers, floats, booleans
- **Collection types** - Lists, dictionaries, sets with full atomic operation support
- **Specialized types** - Enhanced RedisStr, RedisList, RedisDict with IDE autocomplete

You can also create your own custom types or decide how to save the data in redis.
Other types are also supported, essentially we support any type that can be serialized to pickle, however, they can be used to perform atomic operations.

### Atomic Operations for Race Condition Prevention

Every operation in Rapyer is designed to be atomic and safe in concurrent environments:

```python
# All operations are atomic - no race conditions possible
await user.tags.aappend("python")           # Atomic list append
await user.metadata.aupdate(role="dev")     # Atomic dict update
user.score += 10; await user.score.save()  # Atomic increment
```

For complex multi-field operations, Rapyer provides lock context managers and pipeline operations that ensure consistency across multiple changes.

## Quick Example

```python
import asyncio
from rapyer import AtomicRedisModel
from typing import List, Dict

class User(AtomicRedisModel):
    name: str
    age: int
    tags: List[str] = []
    metadata: Dict[str, str] = {}

async def main():
    # Create and save
    user = User(name="Alice", age=25)
    await user.save()

    # Atomic operations
    await user.tags.aappend("developer")
    await user.tags.aextend(["python", "redis"])
    await user.metadata.aupdate(team="backend", level="senior")

    # Load and verify
    loaded = await User.get(user.key)
    print(f"User: {loaded.name}, Tags: {loaded.tags}")

if __name__ == "__main__":
    asyncio.run(main())
```

This example demonstrates Rapyer's core philosophy: combine Redis performance with Pydantic safety, all while maintaining atomic operations that prevent data corruption in concurrent applications.
