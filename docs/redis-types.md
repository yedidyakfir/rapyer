# Redis Types for Enhanced IDE Support

Redis Types are specialized type annotations that provide enhanced IDE support and intellisense for Redis-specific operations. Instead of using regular Python types like `str`, `int`, `list`, and `dict` in your model annotations, you can use `RedisStr`, `RedisInt`, `RedisList`, and `RedisDict` to get full autocomplete for all Redis atomic operations.

## Overview

When you use Redis Types in your model annotations, your IDE will recognize all available Redis operations like `aappend()`, `aextend()`, `increase()`, etc., providing better development experience with full type safety.

```python
from rapyer.base import AtomicRedisModel
from rapyer.types.string import RedisStr
from rapyer.types.integer import RedisInt
from rapyer.types.lst import RedisList
from rapyer.types.dct import RedisDict

class UserModel(AtomicRedisModel):
    # Instead of: name: str = ""
    name: RedisStr = ""
    
    # Instead of: age: int = 0  
    age: RedisInt = 0
    
    # Instead of: tags: List[str] = []
    tags: RedisList[str] = Field(default_factory=list)
    
    # Instead of: metadata: Dict[str, str] = {}
    metadata: RedisDict[str, str] = Field(default_factory=dict)
```

## Available Redis Types

### RedisStr

Provides enhanced IDE support for string operations.

```python
from rapyer.types.string import RedisStr

class DocumentModel(AtomicRedisModel):
    title: RedisStr = "Untitled"
    content: RedisStr = ""

# Usage
doc = DocumentModel()
await doc.save()

# IDE will show all available string operations
doc.title = "New Title"
await doc.title.save()  # ✓ IDE autocomplete available
```

**Available operations:**
- `save()` - Save to Redis
- `load()` - Load from Redis  
- `clone()` - Create a copy

### RedisInt

Provides enhanced IDE support for integer operations, including the atomic `increase()` method.

```python
from rapyer.types.integer import RedisInt

class CounterModel(AtomicRedisModel):
    views: RedisInt = 0
    likes: RedisInt = 0

# Usage  
counter = CounterModel()
await counter.save()

# IDE will show integer-specific operations
await counter.views.increase(1)    # ✓ IDE autocomplete for increase()
await counter.likes.increase(5)    # ✓ Atomic increment operation
counter.views = 100
await counter.views.save()         # ✓ Direct assignment and save
```

**Available operations:**
- `save()` - Save to Redis
- `load()` - Load from Redis
- `increase(amount=1)` - Atomic increment operation
- `clone()` - Create a copy

### RedisList[T]

Provides enhanced IDE support for all Redis list operations with full type safety.

```python
from rapyer.types.lst import RedisList
from typing import List
from pydantic import Field

class TaskModel(AtomicRedisModel):
    tasks: RedisList[str] = Field(default_factory=list)
    priorities: RedisList[int] = Field(default_factory=list)

# Usage
task_model = TaskModel()
await task_model.save()

# IDE will show all Redis list operations with proper typing
await task_model.tasks.aappend("Buy groceries")       # ✓ Autocomplete
await task_model.tasks.aextend(["Walk dog", "Cook"])  # ✓ Type checking
await task_model.tasks.ainsert(0, "Wake up")          # ✓ Insert at index
first_task = await task_model.tasks.apop(0)           # ✓ Pop with return type
await task_model.tasks.aclear()                       # ✓ Clear list

# Index assignment (automatic atomic operation)
task_model.tasks[0] = "Updated task"  # ✓ IDE knows this is str
```

**Available atomic operations:**
- `aappend(item)` - Add item to end
- `aextend(items)` - Add multiple items
- `ainsert(index, item)` - Insert at specific index  
- `apop(index=-1)` - Remove and return item
- `aclear()` - Remove all items
- `save()` - Save entire list
- `load()` - Load from Redis
- `clone()` - Create a copy

### RedisDict[K, V]

Provides enhanced IDE support for all Redis dictionary operations with full type safety.

```python
from rapyer.types.dct import RedisDict
from typing import Dict
from pydantic import Field

class UserProfileModel(AtomicRedisModel):
    settings: RedisDict[str, str] = Field(default_factory=dict)
    scores: RedisDict[str, int] = Field(default_factory=dict)

# Usage
profile = UserProfileModel()
await profile.save()

# IDE will show all Redis dict operations with proper typing
await profile.settings.aset_item("theme", "dark")           # ✓ Autocomplete
await profile.settings.aupdate(language="en", timezone="UTC") # ✓ Type checking
theme = await profile.settings.apop("theme")                # ✓ Pop with return
await profile.settings.adel_item("old_setting")             # ✓ Delete key
key_value = await profile.settings.apopitem()               # ✓ Pop arbitrary item
await profile.settings.aclear()                             # ✓ Clear dictionary

# Key assignment (automatic atomic operation)
profile.settings["new_key"] = "new_value"  # ✓ IDE knows this is str -> str
profile.scores["high_score"] = 9999        # ✓ IDE knows this is str -> int
```

**Available atomic operations:**
- `aset_item(key, value)` - Set key-value pair
- `adel_item(key)` - Delete key
- `aupdate(**kwargs)` - Update multiple pairs
- `apop(key, default=None)` - Remove and return value
- `apopitem()` - Remove and return arbitrary pair
- `aclear()` - Remove all items
- `save()` - Save entire dictionary
- `load()` - Load from Redis
- `clone()` - Create a copy

### RedisBytes

Provides enhanced IDE support for bytes operations.

```python
from rapyer.types.byte import RedisBytes

class FileModel(AtomicRedisModel):
    file_data: RedisBytes = b""
    thumbnail: RedisBytes = b""

# Usage
file_model = FileModel(file_data=b"binary content")
await file_model.save()

# IDE will show bytes-specific operations
file_model.file_data = b"updated content"
await file_model.file_data.save()  # ✓ IDE autocomplete available
```

**Available operations:**
- `save()` - Save to Redis
- `load()` - Load from Redis
- `clone()` - Create a copy

## IDE Benefits

### Autocomplete and IntelliSense

When using Redis Types, your IDE will provide full autocomplete for Redis-specific operations:

```python
class ExampleModel(AtomicRedisModel):
    tags: RedisList[str] = Field(default_factory=list)
    metadata: RedisDict[str, str] = Field(default_factory=dict)

model = ExampleModel()

# IDE will suggest these Redis operations:
await model.tags.a   # → aappend, aextend, ainsert, apop, aclear
await model.metadata.a  # → aset_item, adel_item, aupdate, apop, apopitem, aclear
```

### Type Safety

Redis Types provide the same type safety as regular Python types but with enhanced Redis operation support:

```python
class TypedModel(AtomicRedisModel):
    numbers: RedisList[int] = Field(default_factory=list)
    mappings: RedisDict[str, int] = Field(default_factory=dict)

model = TypedModel()

# Type checking works as expected
await model.numbers.aappend(42)        # ✓ int is valid
await model.numbers.aappend("text")    # ✗ Type error: str not compatible with int

await model.mappings.aset_item("key", 100)  # ✓ str -> int is valid  
await model.mappings.aset_item("key", "val") # ✗ Type error: str not compatible with int
```

### Error Detection

IDEs can detect incorrect usage at development time:

```python
class UserModel(AtomicRedisModel):
    name: RedisStr = ""
    tags: RedisList[str] = Field(default_factory=list)

user = UserModel()

# IDE will warn about these errors:
await user.name.aappend("text")    # ✗ Error: RedisStr has no aappend method
await user.tags.increase(1)        # ✗ Error: RedisList has no increase method
```

## Comparison: Regular Types vs Redis Types

### Regular Type Annotations

```python
from typing import List, Dict

class RegularModel(AtomicRedisModel):
    name: str = ""
    age: int = 0
    tags: List[str] = []
    metadata: Dict[str, str] = {}

model = RegularModel()

# Limited IDE support - you need to remember Redis operations
await model.tags.aappend("python")    # Works, but no autocomplete for 'aappend'
await model.metadata.aupdate(key="value")  # Works, but no autocomplete for 'aupdate'
```

### Redis Type Annotations

```python
from rapyer.types.string import RedisStr
from rapyer.types.integer import RedisInt  
from rapyer.types.lst import RedisList
from rapyer.types.dct import RedisDict

class RedisTypedModel(AtomicRedisModel):
    name: RedisStr = RedisStr("")
    age: RedisInt = RedisInt(0)
    tags: RedisList[str] = Field(default_factory=list)
    metadata: RedisDict[str, str] = Field(default_factory=dict)

model = RedisTypedModel()

# Full IDE support with autocomplete
await model.tags.aappend("python")         # ✓ Full autocomplete available
await model.metadata.aupdate(key="value")  # ✓ Full autocomplete available
await model.age.increase(1)                # ✓ Shows increase() method
```

## Usage Patterns

### Mixed Type Usage

You can mix regular types and Redis Types in the same model based on your needs:

```python
class MixedModel(AtomicRedisModel):
    # Use Redis Types where you need enhanced IDE support
    active_tasks: RedisList[str] = Field(default_factory=list)
    user_settings: RedisDict[str, str] = Field(default_factory=dict)
    view_count: RedisInt = 0
    
    # Use regular types for simple fields  
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    description: str = ""

# Both approaches work identically at runtime
mixed = MixedModel()
await mixed.active_tasks.aappend("task1")  # ✓ Redis Type with autocomplete
mixed.is_active = False                    # ✓ Regular type works fine
await mixed.save()
```

### Generic Type Parameters

Redis Types support full generic type parameters:

```python
from typing import Union

class AdvancedModel(AtomicRedisModel):
    # Complex generic types work perfectly
    string_lists: RedisList[List[str]] = Field(default_factory=list)
    nested_mappings: RedisDict[str, Dict[str, int]] = Field(default_factory=dict)
    union_values: RedisList[Union[str, int]] = Field(default_factory=list)

advanced = AdvancedModel()

# Full type safety maintained
await advanced.string_lists.aappend(["item1", "item2"])  # ✓ List[str] 
await advanced.nested_mappings.aset_item("key", {"score": 100})  # ✓ Dict[str, int]
await advanced.union_values.aextend(["text", 42, "more"])  # ✓ Union types
```

## When to Use Redis Types

### Recommended Use Cases

✅ **Active Development**: When you're actively developing and want full IDE support  
✅ **Complex Operations**: Models with frequent Redis list/dict operations  
✅ **Team Development**: When working in teams where autocomplete helps productivity  
✅ **Learning**: When learning Rapyer's Redis operations

### Optional Use Cases

⚪ **Simple Models**: Models with mostly primitive fields (str, int, bool)  
⚪ **Production Code**: Once development is complete, both approaches work identically  
⚪ **Migration**: Existing code with regular types works perfectly

## Performance Considerations

Redis Types have **identical runtime performance** to regular types. The only difference is enhanced IDE support during development.

```python
# These models have identical performance characteristics:

class RegularModel(AtomicRedisModel):
    tags: List[str] = []

class RedisTypedModel(AtomicRedisModel):  
    tags: RedisList[str] = Field(default_factory=list)

# Both execute the same Redis operations at runtime
regular = RegularModel()
redis_typed = RedisTypedModel()

await regular.tags.aappend("item")      # Same Redis operation
await redis_typed.tags.aappend("item")  # Same Redis operation
```

## Migration Guide

### Converting Existing Models

You can easily convert existing models to use Redis Types:

```python
# Before: Regular types
class OldModel(AtomicRedisModel):
    name: str = ""
    count: int = 0
    items: List[str] = []
    data: Dict[str, int] = {}

# After: Redis Types (optional conversion)
from rapyer.types.string import RedisStr
from rapyer.types.integer import RedisInt
from rapyer.types.lst import RedisList
from rapyer.types.dct import RedisDict

class NewModel(AtomicRedisModel):
    name: RedisStr = ""
    count: RedisInt = 0
    items: RedisList[str] = Field(default_factory=list)
    data: RedisDict[str, int] = Field(default_factory=dict)
```

### Gradual Migration

You don't need to convert all fields at once:

```python
class PartiallyMigratedModel(AtomicRedisModel):
    # Converted to Redis Types for better IDE support
    active_tasks: RedisList[str] = Field(default_factory=list)
    settings: RedisDict[str, str] = Field(default_factory=dict)
    
    # Keep as regular types (still works perfectly)
    name: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
```

## Best Practices

### IDE Configuration

Ensure your IDE is configured for optimal Python type checking:

- **PyCharm**: Enable type checking in Settings → Editor → Inspections → Python → Type checker
- **VS Code**: Use Pylance extension with type checking enabled
- **Other IDEs**: Enable Python type hints and autocomplete features

### Import Organization

Keep Redis Type imports organized:

```python
# Recommended import style
from rapyer.base import AtomicRedisModel
from rapyer.types.string import RedisStr
from rapyer.types.integer import RedisInt
from rapyer.types.lst import RedisList
from rapyer.types.dct import RedisDict
from pydantic import Field
from typing import List, Dict  # For regular types if needed
```

### Documentation

Document your models clearly when using Redis Types:

```python
class UserModel(AtomicRedisModel):
    """User model with enhanced Redis Type support for better IDE experience."""
    
    name: RedisStr = ""                              # User's display name
    login_count: RedisInt = 0                        # Number of logins (with atomic increment)
    permissions: RedisList[str] = Field(default_factory=list) # User permissions (with Redis operations)
    preferences: RedisDict[str, str] = Field(default_factory=dict)  # User settings (with Redis operations)
```

## Conclusion

Redis Types provide enhanced IDE support and developer experience while maintaining identical runtime behavior to regular Python types. They are particularly valuable during active development and when working with complex Redis operations.

Choose Redis Types when:
- You want full autocomplete for Redis operations
- You're actively developing with frequent Redis list/dict operations  
- You're working in a team environment where IDE support improves productivity
- You're learning Rapyer's Redis capabilities

Regular types remain perfectly valid and performant for all use cases. The choice between regular types and Redis Types is purely about development experience preferences.