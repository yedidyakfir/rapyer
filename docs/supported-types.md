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

**Operations:**
- `save()` - Save to Redis
- `load()` - Load from Redis

```python
class User(AtomicRedisModel):
    name: str
    bio: str = ""

user = User(name="John", bio="Developer")
await user.save()

# Update string values
user.name = "John Doe"
await user.name.save()
user.bio = "Senior Python Developer"
await user.bio.save()
```

### Integer (`int`)

**Operations:**
- `save()` - Save to Redis
- `load()` - Load from Redis
- `increase(amount=1)` - Atomic increment operation

```python
class Counter(AtomicRedisModel):
    count: int = 0
    score: int = 0

counter = Counter()
await counter.save()

# Update integer values
counter.count = 42
await counter.count.save()
counter.score = 100
await counter.score.save()

# Atomic increment operations
await counter.count.increase(10)  # Increments count by 10
await counter.score.increase()    # Increments score by 1 (default)
```

### Boolean (`bool`)

**Operations:**
- `save()` - Save to Redis
- `load()` - Load from Redis

```python
class Settings(AtomicRedisModel):
    is_active: bool = True
    debug_mode: bool = False

settings = Settings()
await settings.save()

# Update boolean values
settings.is_active = False
await settings.is_active.save()
settings.debug_mode = True
await settings.debug_mode.save()
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
todo.tasks = ["New task 1", "New task 2"]
await todo.tasks.save()
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
profile.metadata = {"status": "active", "tier": "premium"}
await profile.metadata.save()
```

**Dictionary Item Assignment:**
```python
# Direct key assignment (atomic)
profile.metadata["new_key"] = "new_value"  # Automatically atomic
profile.scores["high_score"] = 9999
```

### Bytes (`bytes`)

**Operations:**
- `save()` - Save to Redis
- `load()` - Load from Redis

```python
class FileModel(AtomicRedisModel):
    file_data: bytes
    thumbnail: bytes = b""

file_model = FileModel(file_data=b"binary content")
await file_model.save()

# Update bytes values
file_model.file_data = b"updated binary content"
await file_model.file_data.save()
file_model.thumbnail = b"thumbnail data"
await file_model.thumbnail.save()
```

### DateTime (`datetime`)

**Operations:**
- `save()` - Save to Redis
- `load()` - Load from Redis

```python
from datetime import datetime

class Event(AtomicRedisModel):
    created_at: datetime
    updated_at: datetime = None

event = Event(created_at=datetime.now())
await event.save()

# Update datetime values
event.updated_at = datetime.now()
await event.updated_at.save()
event.created_at = datetime(2023, 1, 1, 12, 0, 0)
await event.created_at.save()
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

# Update complex types
new_address = Address("456 Oak Ave", "Cambridge", "02139")
user.address = new_address
await user.address.save()
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

# Update enum values
app.status = Status.APPROVED
await app.status.save()
```

### Union Types

```python
from typing import Union

class FlexibleModel(AtomicRedisModel):
    value: Union[int, str, float]
    optional_data: Union[Dict[str, str], List[str], None] = None

model = FlexibleModel(value=42)
await model.save()

# Update union type values
model.value = "now a string"
await model.value.save()
model.value = 3.14
await model.value.save()
model.optional_data = {"key": "value"}
await model.optional_data.save()
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

# Update custom objects
app.config = CustomConfig(debug=False, timeout=120)
await app.config.save()
```

### BaseModel (Nested Models)

**Operations:**
- `save()` - Save to Redis
- `load()` - Load from Redis
- `aupdate(**kwargs)` - Atomically update multiple fields
- `update(**kwargs)` - Update multiple fields (non-atomic)
- `duplicate()` - Create a copy
- `delete()` - Delete from Redis

```python
class UserProfile(AtomicRedisModel):
    first_name: str
    last_name: str
    email: str

class User(AtomicRedisModel):
    username: str
    profile: UserProfile
    is_active: bool = True

user = User(
    username="johndoe",
    profile=UserProfile(
        first_name="John",
        last_name="Doe", 
        email="john@example.com"
    )
)
await user.save()

# Update nested model fields atomically
await user.profile.aupdate(
    first_name="Jonathan",
    email="jonathan@example.com"
)

# Update entire nested model
new_profile = UserProfile(
    first_name="Jane",
    last_name="Smith",
    email="jane@example.com"
)
user.profile = new_profile
await user.profile.save()
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

## Type Behavior Summary

### Primitive Types vs Complex Types

**Primitive Types** (`str`, `int`, `bool`, `bytes`, `datetime`):
- Updated via direct assignment: `model.field = new_value`
- Persisted via: `await model.field.save()`
- Special atomic operations: `increase()` for integers

**Complex Types** (`List`, `Dict`, nested models):
- Updated via atomic operations: `await model.list.aappend(item)`
- Operations update both Redis and Python model automatically
- Support index assignment: `model.list[0] = new_value`

```python
class User(AtomicRedisModel):
    name: str = "John"
    age: int = 25
    tags: List[str] = []
    metadata: Dict[str, str] = {}

user = User()
await user.save()

# Primitive type updates
user.name = "Jane"
await user.name.save()  # Persists to Redis

# Integer atomic operations
await user.age.increase(1)  # Atomic increment

# Complex type operations (update both Redis and model)
await user.tags.aappend("python")
await user.metadata.aupdate(role="admin")

# Load all fields from Redis
await user.load()  # Syncs all fields from Redis
```

| Type | Storage | Operations | Assignment | Atomic Operations |
|------|---------|------------|------------|------------------|
| `str` | Native | `save()`, `load()` | Direct | - |
| `int` | Native | `save()`, `load()`, `increase()` | Direct | `increase()` |
| `bool` | Native | `save()`, `load()` | Direct | - |
| `bytes` | Native | `save()`, `load()` | Direct | - |
| `datetime` | Native | `save()`, `load()` | Direct | - |
| `List[T]` | Native | All list atomic ops | Index assignment | `aappend()`, `aextend()`, etc. |
| `Dict[K,V]` | Native | All dict atomic ops | Key assignment | `aupdate()`, `aset_item()`, etc. |
| `BaseModel` | Native | `save()`, `load()`, `aupdate()`, `update()` | Direct | `aupdate()` |
| Custom Types | Serialized | `save()`, `load()` | Direct | - |

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