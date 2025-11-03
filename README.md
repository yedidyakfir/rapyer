<div align="center">
  <img src="icon.png" alt="Rapyer Logo" width="120">
  
  # Rapyer
  
  **Redis Atomic Pydantic Engine Reactor**
  
  *An async Redis ORM that provides atomic operations for complex data models*
  
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Redis](https://img.shields.io/badge/redis-6.0+-red.svg)](https://redis.io/)
  [![codecov](https://codecov.io/gh/yedidyakfir/rapyer/branch/main/graph/badge.svg)](https://codecov.io/gh/yedidyakfir/rapyer)
  
  📚 **[Full Documentation](https://yedidyakfir.github.io/rapyer/)** | [Installation](https://yedidyakfir.github.io/rapyer/installation/) | [Examples](https://yedidyakfir.github.io/rapyer/examples/) | [API Reference](https://yedidyakfir.github.io/rapyer/api/)
</div>

---

## What is Rapyer?

Rapyer (**R**edis **A**tomic **Py**dantic **E**ngine **R**eactor) is a modern async Redis ORM that enables atomic operations on complex data models. Built with Pydantic v2, it provides type-safe Redis interactions while maintaining data consistency and preventing race conditions.

### Key Features

🚀 **Atomic Operations** - Built-in atomic updates for complex Redis data structures  
⚡ **Async/Await** - Full asyncio support for high-performance applications  
🔒 **Type Safety** - Complete type validation using Pydantic v2  
🌐 **Universal Types** - Native optimization for primitives, automatic serialization for complex types  
🔄 **Race Condition Safe** - Lock context managers and pipeline operations  
📦 **Redis JSON** - Efficient storage using Redis JSON with support for nested structures

## Installation

```bash
pip install rapyer
```

**Requirements:**
- Python 3.10+
- Redis server with JSON module
- Pydantic v2

## Quick Start

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

    # Atomic operations with locks for complex updates
    async with user.lock("update_profile") as locked_user:
        locked_user.age += 1
        await locked_user.tags.aappend("experienced")
        # Changes saved atomically when context exits

if __name__ == "__main__":
    asyncio.run(main())
```

## Core Concepts

### Atomic Operations
Rapyer ensures data consistency with built-in atomic operations:

```python
# These operations are atomic and race-condition safe
await user.tags.aappend("python")           # Add to list
await user.metadata.aupdate(role="dev")     # Update dict
await user.score.set(100)                   # Set value
```

### Lock Context Manager
For complex multi-field updates:

```python
async with user.lock("transaction") as locked_user:
    locked_user.balance -= 50
    locked_user.transaction_count += 1
    # All changes saved atomically
```

### Pipeline Operations
Batch multiple operations for performance:

```python
async with user.pipeline() as pipelined_user:
    await pipelined_user.tags.aappend("redis")
    await pipelined_user.metadata.aupdate(level="senior")
    # Executed as single atomic transaction
```

## Type Support

Rapyer supports all Python types with automatic serialization:

- **Native types** (`str`, `int`, `List`, `Dict`) - Optimized Redis operations
- **Complex types** (`dataclass`, `Enum`, `Union`) - Automatic pickle serialization  
- **Nested models** - Full Redis functionality preserved

```python
from dataclasses import dataclass
from enum import Enum

@dataclass
class Config:
    debug: bool = False

class User(AtomicRedisModel):
    name: str = "default"
    scores: List[int] = []
    config: Config = Config()  # Auto-serialized
    
# All types work identically
user = User()
await user.config.set(Config(debug=True))  # Automatic serialization
await user.scores.aappend(95)               # Native Redis operation
```

## Why Rapyer?

### Race Condition Prevention
Traditional Redis operations can lead to data inconsistency in concurrent environments. Rapyer solves this with atomic operations and lock management.

### Developer Experience  
- **Type Safety**: Full Pydantic v2 validation
- **Async/Await**: Native asyncio support
- **Intuitive API**: Pythonic Redis operations

### Performance
- **Pipeline Operations**: Batch multiple operations
- **Native Type Optimization**: Efficient Redis storage
- **Connection Pooling**: Built-in Redis connection management

## Learn More

- 📖 **[Documentation](https://yedidyakfir.github.io/rapyer/)** - Complete guide and API reference
- 🚀 **[Examples](https://yedidyakfir.github.io/rapyer/examples/)** - Real-world usage patterns  
- ⚡ **[Advanced Features](https://yedidyakfir.github.io/rapyer/advanced/)** - Locks, pipelines, and nested models
- 🗺️ **[Roadmap](https://yedidyakfir.github.io/rapyer/roadmap/)** - Future features and development plans

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
Thanks for [@Mizaro](https://github.com/Mizaro) this would not have been possible without you. 

## License

MIT License