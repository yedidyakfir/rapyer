# Rapyer - Redis Atomic Pydantic Engine Reactor

<div align="center">
  <img src="icon.png" alt="Rapyer Logo" width="120">
</div>

**Rapyer** is a modern async Redis ORM that provides atomic operations for complex data models with full type safety. Built on Pydantic v2, it ensures data consistency and prevents race conditions in concurrent environments.

## What Makes Rapyer Special?

Rapyer solves the critical problem of race conditions in Redis operations while maintaining a Pythonic, type-safe API. Unlike traditional Redis clients, Rapyer guarantees atomic operations for complex data structures.

### Key Features

🚀 **Atomic Operations** - Built-in atomic updates prevent race conditions  
⚡ **Async/Await** - Full asyncio support for high-performance applications  
🔒 **Type Safety** - Complete type validation using Pydantic v2  
🌐 **Universal Types** - Native optimization for primitives, automatic serialization for complex types  
🔄 **Race Condition Safe** - Lock context managers and pipeline operations  
📦 **Redis JSON** - Efficient storage using Redis JSON with support for nested structures  
🏗️ **Nested Models** - Full Redis functionality preserved in nested structures

## Quick Example

```python
import asyncio
from rapyer.base import AtomicRedisModel
from typing import List, Dict

class User(AtomicRedisModel):
    name: str
    age: int
    tags: List[str] = []
    metadata: Dict[str, str] = {}

async def main():
    # Create and save a user
    user = User(name="John", age=30)
    await user.save()

    # Atomic operations that prevent race conditions
    await user.tags.aappend("python")
    await user.tags.aextend(["redis", "pydantic"])
    await user.metadata.aupdate(role="developer", level="senior")

    # Load user from Redis
    loaded_user = await User.get(user.key)
    print(f"User: {loaded_user.name}, Tags: {loaded_user.tags}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Core Concepts

### Atomic Operations
Every operation in Rapyer is designed to be atomic and race-condition safe:

```python
# These operations are atomic and safe in concurrent environments
await user.tags.aappend("python")           # Add to list atomically
await user.metadata.aupdate(role="dev")     # Update dict atomically
await user.age.set(31)                      # Set value atomically
```

### Lock Context Manager
For complex multi-field updates that require consistency:

```python
async with user.lock("transaction") as locked_user:
    locked_user.balance -= 50
    locked_user.transaction_count += 1
    # All changes saved atomically when context exits
```

### Pipeline Operations
Batch multiple operations for maximum performance:

```python
async with user.pipeline() as pipelined_user:
    await pipelined_user.tags.aappend("redis")
    await pipelined_user.metadata.aupdate(level="senior")
    # Executed as single atomic transaction
```

## Why Choose Rapyer?

### Race Condition Prevention
Traditional Redis operations can lead to data inconsistency in concurrent environments. Rapyer's atomic operations ensure data integrity even under high concurrency.

### Developer Experience  
- **Type Safety**: Full Pydantic v2 validation with IDE support
- **Async/Await**: Native asyncio integration  
- **Intuitive API**: Pythonic Redis operations that feel natural

### Performance
- **Pipeline Operations**: Batch multiple operations efficiently
- **Native Type Optimization**: Optimized Redis storage for common types
- **Connection Pooling**: Built-in Redis connection management

## Getting Started

Ready to build race-condition-free Redis applications? Start with our [Setup Guide](setup.md) to get Rapyer installed and configured in minutes.

## Navigation

- **[Setup](setup.md)** - Installation and configuration
- **[Basic Operations](basic-operations.md)** - Save, load, get, delete operations
- **[Supported Types](supported-types.md)** - Complete type support and atomic actions
- **[Atomic Actions](atomic-actions.md)** - Locks, pipelines, and concurrency safety
- **[Nested Models](nested-models.md)** - Working with complex nested structures