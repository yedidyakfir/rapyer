# Supported Types and Atomic Actions

Rapyer supports a wide range of Python types with optimized Redis operations. This guide covers all supported types and their available atomic actions.

## Type Categories

Rapyer handles types in three categories:

1. **Native Types** - Optimized for Redis with native atomic operations
2. **Complex Types** - Automatically serialized with full functionality  
3. **Nested Models** - Full Redis functionality preserved in nested structures

## Native Types

Native types have optimized Redis storage and specialized atomic operations.

### String (`str`)

**Atomic Operations:**
- `set(value)` - Set string value
- `load()` - Load from Redis

```python
class User(AtomicRedisModel):
    name: str
    bio: str = ""

user = User(name="John", bio="Developer")
await user.save()

# Atomic string operations
await user.name.set("John Doe")
await user.bio.set("Senior Python Developer")
```

### Integer (`int`)

**Atomic Operations:**
- `set(value)` - Set integer value
- `load()` - Load from Redis

```python
class Counter(AtomicRedisModel):
    count: int = 0
    score: int = 0

counter = Counter()
await counter.save()

# Atomic integer operations
await counter.count.set(42)
await counter.score.set(100)
```

### Boolean (`bool`)

**Atomic Operations:**
- `set(value)` - Set boolean value
- `load()` - Load from Redis

```python
class Settings(AtomicRedisModel):
    is_active: bool = True
    debug_mode: bool = False

settings = Settings()
await settings.save()

# Atomic boolean operations
await settings.is_active.set(False)
await settings.debug_mode.set(True)
```

### List (`List[T]`)

**Atomic Operations:**
- `aappend(item)` - Add item to end of list
- `aextend(items)` - Add multiple items to end
- `ainsert(index, item)` - Insert item at specific index
- `apop(index=-1)` - Remove and return item at index
- `aclear()` - Remove all items
- `set(value)` - Replace entire list
- `load()` - Load from Redis

```python
class TodoList(AtomicRedisModel):
    tasks: List[str] = []
    priorities: List[int] = []

todo = TodoList()
await todo.save()

# Atomic list operations
await todo.tasks.aappend("Buy groceries")
await todo.tasks.aextend(["Walk dog", "Read book"])
await todo.tasks.ainsert(0, "Wake up")  # Insert at beginning

# Remove operations
last_task = await todo.tasks.apop()  # Remove last item
first_task = await todo.tasks.apop(0)  # Remove first item

# Clear all tasks
await todo.tasks.aclear()

# Replace entire list
await todo.tasks.set(["New task 1", "New task 2"])
```

**List Item Assignment:**
```python
# Direct index assignment (atomic)
todo.tasks[0] = "Updated first task"  # Automatically atomic
todo.priorities[1] = 5
```

### Dictionary (`Dict[K, V]`)

**Atomic Operations:**
- `aset_item(key, value)` - Set key-value pair
- `adel_item(key)` - Delete key
- `aupdate(**kwargs)` - Update multiple key-value pairs
- `apop(key, default=None)` - Remove and return value for key
- `apopitem()` - Remove and return arbitrary (key, value) pair
- `aclear()` - Remove all items
- `set(value)` - Replace entire dictionary
- `load()` - Load from Redis

```python
class UserProfile(AtomicRedisModel):
    metadata: Dict[str, str] = {}
    scores: Dict[str, int] = {}

profile = UserProfile()
await profile.save()

# Atomic dictionary operations
await profile.metadata.aset_item("role", "admin")
await profile.metadata.aupdate(department="engineering", level="senior")

# Remove operations
role = await profile.metadata.apop("role")  # Remove and get value
key_value = await profile.metadata.apopitem()  # Remove arbitrary item
await profile.metadata.adel_item("department")  # Just remove

# Clear all metadata
await profile.metadata.aclear()

# Replace entire dictionary
await profile.metadata.set({"status": "active", "tier": "premium"})
```

**Dictionary Item Assignment:**
```python
# Direct key assignment (atomic)
profile.metadata["new_key"] = "new_value"  # Automatically atomic
profile.scores["high_score"] = 9999
```

### Bytes (`bytes`)

**Atomic Operations:**
- `set(value)` - Set bytes value
- `load()` - Load from Redis

```python
class FileModel(AtomicRedisModel):
    file_data: bytes
    thumbnail: bytes = b""

file_model = FileModel(file_data=b"binary content")
await file_model.save()

# Atomic bytes operations
await file_model.file_data.set(b"updated binary content")
await file_model.thumbnail.set(b"thumbnail data")
```

### DateTime (`datetime`)

**Atomic Operations:**
- `set(value)` - Set datetime value
- `load()` - Load from Redis

```python
from datetime import datetime

class Event(AtomicRedisModel):
    created_at: datetime
    updated_at: datetime = None

event = Event(created_at=datetime.now())
await event.save()

# Atomic datetime operations
await event.updated_at.set(datetime.now())
await event.created_at.set(datetime(2023, 1, 1, 12, 0, 0))
```

## Complex Types

Complex types are automatically serialized using pickle and support the same atomic operations as native types.

### Dataclasses

```python
from dataclasses import dataclass

@dataclass
class Address:
    street: str
    city: str
    zip_code: str

class User(AtomicRedisModel):
    name: str
    address: Address

user = User(
    name="John",
    address=Address("123 Main St", "Boston", "02101")
)
await user.save()

# Atomic operations on complex types
new_address = Address("456 Oak Ave", "Cambridge", "02139")
await user.address.set(new_address)
```

### Enums

```python
from enum import Enum

class Status(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Application(AtomicRedisModel):
    status: Status = Status.PENDING
    priority: int = 1

app = Application()
await app.save()

# Atomic enum operations
await app.status.set(Status.APPROVED)
```

### Union Types

```python
from typing import Union

class FlexibleModel(AtomicRedisModel):
    value: Union[int, str, float]
    optional_data: Union[Dict[str, str], List[str], None] = None

model = FlexibleModel(value=42)
await model.save()

# Atomic operations work with any union type
await model.value.set("now a string")
await model.value.set(3.14)
await model.optional_data.set({"key": "value"})
```

### Custom Classes

Any serializable Python object:

```python
class CustomConfig:
    def __init__(self, debug=False, timeout=30):
        self.debug = debug
        self.timeout = timeout

class App(AtomicRedisModel):
    config: CustomConfig
    name: str

app = App(
    name="MyApp",
    config=CustomConfig(debug=True, timeout=60)
)
await app.save()

# Atomic operations on custom objects
await app.config.set(CustomConfig(debug=False, timeout=120))
```

## Generic Types with Type Parameters

Rapyer fully supports generic types with proper type checking:

### Generic Lists

```python
from typing import List, TypeVar

# Lists with specific types
class GameData(AtomicRedisModel):
    player_names: List[str] = []
    high_scores: List[int] = []
    game_states: List[dict] = []

game = GameData()
await game.save()

# Type-safe operations
await game.player_names.aappend("Alice")  # str
await game.high_scores.aappend(9999)      # int
await game.game_states.aappend({"level": 1, "lives": 3})  # dict
```

### Generic Dictionaries

```python
from typing import Dict

class Mappings(AtomicRedisModel):
    str_to_int: Dict[str, int] = {}
    int_to_str: Dict[int, str] = {}
    nested_data: Dict[str, List[str]] = {}

mappings = Mappings()
await mappings.save()

# Type-safe dictionary operations
await mappings.str_to_int.aset_item("count", 42)
await mappings.int_to_str.aset_item(1, "first")
await mappings.nested_data.aset_item("tags", ["python", "redis"])
```

## Important: Primitive vs Complex Type Behavior

**⚠️ Critical Distinction:** Primitive types (`str`, `int`, `bool`, `bytes`, `datetime`) have different behavior than complex types (`List`, `Dict`, nested models) when using operations like `set()` and `load()`.

### Primitive Types (str, int, bool, bytes, datetime)

For primitive types, `set()` and `load()` operations **only affect the Redis value**, not the Python model instance:

```python
class User(AtomicRedisModel):
    name: str = "John"
    age: int = 25

user = User()
await user.save()

# ❌ This updates Redis but NOT the Python model
await user.name.set("Jane")
print(user.name)  # Still prints "John" - Python model unchanged!

# ❌ This loads from Redis but does NOT update the Python model
redis_name = await user.name.load()
print(redis_name)  # Prints "Jane" - the Redis value
print(user.name)   # Still prints "John" - Python model unchanged!

# ✅ To update the Python model, you must assign directly:
user.name = "Jane"  # This updates the Python model
await user.save()   # This persists to Redis
```

### Complex Types (List, Dict, nested models)

For complex types, operations **do update** both Redis and the Python model:

```python
class User(AtomicRedisModel):
    tags: List[str] = []
    metadata: Dict[str, str] = {}

user = User()
await user.save()

# ✅ This updates BOTH Redis AND the Python model
await user.tags.aappend("python")
print(user.tags)  # Prints ["python"] - Python model is updated!

# ✅ This updates BOTH Redis AND the Python model  
await user.metadata.aupdate(role="admin")
print(user.metadata)  # Prints {"role": "admin"} - Python model is updated!
```

### Why This Difference Exists

- **Primitive types** are immutable in Python, so operations return new values rather than modifying in place
- **Complex types** (lists, dicts) are mutable and can be modified in place, maintaining reference consistency
- **Nested models** inherit the behavior of complex types

### Best Practices

1. **For primitive types**: Use direct assignment to update the Python model, then save:
   ```python
   user.name = "New Name"  # Updates Python model
   await user.save()       # Persists to Redis
   ```

2. **For complex types**: Use atomic operations which update both:
   ```python
   await user.tags.aappend("new_tag")        # Updates both
   await user.metadata.aupdate(key="value")  # Updates both
   ```

3. **To sync primitive types from Redis**:
   ```python
   await user.load()  # Loads ALL fields from Redis to Python model
   ```

## Type Behavior Summary

| Type | Storage | Atomic Ops | Index Assignment | Complex Nesting | Model Update |
|------|---------|------------|------------------|-----------------|--------------|
| `str` | Native | ✅ | N/A | N/A | Redis only* |
| `int` | Native | ✅ | N/A | N/A | Redis only* |
| `bool` | Native | ✅ | N/A | N/A | Redis only* |
| `bytes` | Native | ✅ | N/A | N/A | Redis only* |
| `datetime` | Native | ✅ | N/A | N/A | Redis only* |
| `List[T]` | Native | ✅ | ✅ | ✅ | Both |
| `Dict[K,V]` | Native | ✅ | ✅ | ✅ | Both |
| Custom Types | Serialized | ✅ | N/A | ✅ | Redis only* |

*\* Use `model.load()` to sync primitive types from Redis to Python model*

## Performance Considerations

### Native vs. Serialized Types

```python
# ✅ Fastest - Native Redis operations
user_tags: List[str] = []
user_scores: Dict[str, int] = {}

# ✅ Fast - Optimized serialization
user_metadata: Dict[str, str] = {}
timestamps: List[datetime] = []

# 🐌 Slower - Full object serialization (but still atomic)
complex_data: List[CustomClass] = []
nested_objects: Dict[str, CustomClass] = {}
```

### Best Practices

1. **Use native types when possible** for maximum performance
2. **Complex types are fine** - atomicity is preserved regardless
3. **Batch operations** using pipelines for multiple changes
4. **Avoid deep nesting** of complex serialized objects

## Error Handling

All atomic operations can raise exceptions:

```python
try:
    await user.tags.aappend("new_tag")
    await user.metadata.aset_item("key", "value")
except Exception as e:
    print(f"Atomic operation failed: {e}")
    # Operation failed atomically - no partial updates
```

## Next Steps

Now that you understand all supported types, learn about:

- **[Atomic Actions](atomic-actions.md)** - Advanced concurrency features and pipeline operations
- **[Nested Models](nested-models.md)** - Working with complex nested structures