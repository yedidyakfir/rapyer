### Comparison with Other Redis ORMs

| Feature | Rapyer | Redis OM | pydantic-redis | orredis |
|---------|--------|----------|----------------|---------|
| **🚀 Atomic Operations** | ✅ Built-in for all operations | ❌ Manual transactions only | ❌ Manual transactions only | ❌ Manual transactions only |
| **🔒 Lock Context Manager** | ✅ Automatic with `async with model.lock()` | ❌ Manual implementation required | ❌ Manual implementation required | ❌ Manual implementation required |
| **⚡ Pipeline Operations** | ✅ True atomic batching with `model.pipeline()` | ⚠️ Basic pipeline support | ❌ No pipeline support | ❌ No pipeline support |
| **🌐 Universal Type Support** | ✅ Native + automatic serialization for any type | ⚠️ HashModel vs JsonModel limitations | ⚠️ Limited complex types | ⚠️ Limited complex types |
| **🔄 Race Condition Safe** | ✅ Built-in prevention with Lua scripts | ❌ Manual implementation required | ❌ Manual implementation required | ❌ Manual implementation required |
| **📦 Redis JSON Native** | ✅ Optimized JSON operations | ✅ Via JsonModel only | ❌ Hash-based | ❌ Hash-based |
| **⚙️ Pydantic v2 Support** | ✅ Full compatibility | ✅ Recent support | ⚠️ Limited support | ⚠️ Basic support |
| **🎯 Type Safety** | ✅ Complete validation | ✅ Good validation | ✅ Good validation | ⚠️ Basic validation |
| **🚪 Official Support** | ❌ Independent project | ✅ Redis official | ❌ Community | ❌ Community |
| **⚡ Performance** | ✅ Optimized operations | ✅ Good performance | ✅ Standard | ✅ Rust-optimized |
| **🔧 Nested Model Support** | ✅ Full Redis functionality preserved | ⚠️ Limited nesting | ✅ Advanced relationships | ⚠️ Basic support |
| **🎛️ Custom Primary Keys** | ✅ Field annotations | ❌ ULIDs only | ✅ Custom fields | ✅ Custom fields |
| **🔍 Query/Search Support** | ⚠️ Basic (roadmap item) | ✅ RediSearch integration | ❌ No search | ❌ No search |

### 🏆 What Makes Rapyer Unique

#### **True Atomic Operations Out of the Box**
```python
# Rapyer - Atomic by default
await user.tags.aappend("python")           # Race-condition safe
await user.metadata.aupdate(role="dev")     # Always atomic

# Others - Manual transaction management required
async with redis.pipeline() as pipe:        # Manual setup
    pipe.multi()                             # Manual transaction
    # ... manual Redis commands               # Error-prone
    await pipe.execute()
```

#### **Intelligent Lock Management**
```python
# Rapyer - Automatic lock context
async with user.lock("profile_update") as locked_user:
    locked_user.balance -= 50
    locked_user.transaction_count += 1
    # All changes saved atomically on exit

# Others - Manual lock implementation
lock_key = f"lock:{user.key}"
while not await redis.set(lock_key, token, nx=True):  # Manual retry logic
    await asyncio.sleep(0.1)                           # Race conditions possible
# ... manual cleanup required
```

#### **Universal Type System**
```python
# Rapyer - Any Python type works identically
class User(AtomicRedisModel):
    scores: List[int] = []              # Native Redis operations
    config: MyDataClass = MyDataClass()  # Auto-serialized
    metadata: Dict[str, Any] = {}       # Native Redis operations

# All types support the same atomic operations
await user.config.set(new_config)      # Automatic serialization
await user.scores.aappend(95)           # Native Redis LIST operations
await user.metadata.aupdate(key="val") # Native Redis JSON operations
```

#### **Pipeline with True Atomicity**
```python
# Rapyer - Everything in pipeline is atomic
async with user.pipeline() as pipelined_user:
    await pipelined_user.tags.aappend("redis")
    await pipelined_user.metadata.aupdate(level="senior")
    # Single atomic transaction - either all succeed or all fail

# Others - No built-in pipeline abstraction for ORM operations
```

### When to Choose Each

- **Choose Rapyer** if you need:
  - Built-in race condition prevention
  - True atomic operations without manual transaction management
  - Support for any Python type with consistent API
  - Automatic lock management for complex updates

- **Choose Redis OM** if you need:
  - Official Redis support and ecosystem
  - Advanced search/indexing with RediSearch
  - Established community and long-term support

- **Choose pydantic-redis** if you need:
  - Advanced relationship modeling between objects
  - Simple use cases without complex concurrency requirements

- **Choose orredis** if you need:
  - Maximum performance for high-throughput applications
  - Rust-level optimization for Redis operations