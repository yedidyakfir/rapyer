# Supported Types

RedisPydantic supports **all Python types** with automatic Redis serialization and type validation. Types fall into two categories:

1. **Natively supported types** - Optimized Redis storage with native operations
2. **All other types** - Automatically handled using pickle serialization

!!! info "Universal Type Support"
    Any Python type can be used as a field type. Unmapped types are automatically serialized using Python's pickle module and stored as base64-encoded strings in Redis. While this works for any type, natively supported types offer better performance and Redis-native operations.

## Natively Supported Types

The following types have optimized Redis storage and native operations:

### Primitive Types

### String (RedisStr)

```python
class MyModel(BaseRedisModel):
    name: str = "default"
    description: str

# Operations
await model.name.set("new_value")
await model.name.load()
value = model.name  # Access current value
```

### Integer (RedisInt)

```python
class MyModel(BaseRedisModel):
    count: int = 0
    score: int

# Operations  
await model.count.set(42)
await model.count.increase(5)      # Increase by 5
await model.count.increase()       # Increase by 1 (default)
await model.count.increase(-3)     # Decrease by 3
await model.count.load()
current_count = model.count
```

### Boolean (RedisBool)

```python
class MyModel(BaseRedisModel):
    is_active: bool = True
    is_verified: bool

# Operations
await model.is_active.set(False)
await model.is_active.load()
status = model.is_active
```

### Bytes (RedisBytes)

```python
class MyModel(BaseRedisModel):
    data: bytes = b""
    binary_content: bytes

# Operations
await model.data.set(b"binary_data")
await model.data.load()
content = model.data  # Returns bytes object
```

!!! note "Bytes Serialization"
    Bytes are automatically base64 encoded when stored in Redis and decoded when loaded.

### Datetime (RedisDatetime)

```python
from datetime import datetime

class MyModel(BaseRedisModel):
    created_at: datetime = datetime.now()
    updated_at: datetime

# Operations
await model.created_at.set(datetime(2023, 12, 25, 10, 30))
await model.created_at.load()
timestamp = model.created_at  # Returns datetime object
```

!!! note "Datetime Serialization"
    Datetime objects are automatically serialized to ISO format strings in Redis and parsed back to datetime objects when loaded.

## Collection Types

### List (RedisList)

```python
class MyModel(BaseRedisModel):
    tags: List[str] = []
    numbers: List[int] = []
    items: List[Any] = []

# Available operations
await model.tags.aappend("new_tag")              # Add single item
await model.tags.aextend(["tag1", "tag2"])       # Add multiple items
await model.tags.ainsert(0, "first")             # Insert at index
item = await model.tags.apop()                   # Remove and return last
item = await model.tags.apop(0)                  # Remove and return at index
await model.tags.aclear()                        # Clear all items
await model.tags.load()                          # Load from Redis

# Access current state
current_tags = model.tags  # List[str]
```

### Dictionary (RedisDict)

```python
class MyModel(BaseRedisModel):
    metadata: Dict[str, str] = {}
    settings: Dict[str, bool] = {}
    counters: Dict[str, int] = {}

# Available operations
await model.metadata.aset_item("key", "value")           # Set single item
await model.metadata.aupdate(k1="v1", k2="v2")          # Update multiple
await model.metadata.adel_item("key")                    # Delete item
value = await model.metadata.apop("key")                 # Remove and return
value = await model.metadata.apop("key", "default")      # With default
key, value = await model.metadata.apopitem()             # Remove arbitrary item
await model.metadata.aclear()                            # Clear all items
await model.metadata.load()                              # Load from Redis

# Access current state
current_meta = model.metadata  # Dict[str, str]
```

## Nested Types

### Nested Collections

```python
class MyModel(BaseRedisModel):
    # List of lists
    matrix: List[List[int]] = []
    
    # Dict of lists  
    categories: Dict[str, List[str]] = {}
    
    # List of dicts
    records: List[Dict[str, str]] = []

# Operations work on the outer collection
await model.categories.aset_item("python", ["web", "data", "ml"])
await model.matrix.aappend([1, 2, 3])
```

### Nested Models

RedisPydantic automatically supports nested Pydantic models:

```python
from pydantic import BaseModel, Field

class Address(BaseModel):
    street: str
    city: str
    country: str = "US"

class UserProfile(BaseModel):
    bio: str = ""
    skills: List[str] = Field(default_factory=list)
    preferences: Dict[str, bool] = Field(default_factory=dict)

class User(BaseRedisModel):
    name: str
    address: Address
    profile: UserProfile = Field(default_factory=UserProfile)

user = User(
    name="John",
    address=Address(street="123 Main St", city="Boston")
)
await user.save()

# Redis operations work on nested model fields
await user.profile.skills.aappend("Python")
await user.profile.skills.aextend(["Redis", "FastAPI"])
await user.profile.preferences.aupdate(dark_mode=True, notifications=False)

# Load nested fields
await user.profile.skills.load()
await user.address.load()  # Load entire nested model
```

### Deep Nesting

Unlimited nesting depth is supported:

```python
class DeepModel(BaseModel):
    items: List[str] = Field(default_factory=list)
    counter: int = 0

class MiddleModel(BaseModel):
    deep: DeepModel = Field(default_factory=DeepModel)
    tags: List[str] = Field(default_factory=list)

class TopModel(BaseRedisModel):
    middle: MiddleModel = Field(default_factory=MiddleModel)
    data: Dict[str, int] = Field(default_factory=dict)

model = TopModel()
await model.save()

# Operations at any nesting level
await model.middle.deep.items.aappend("deep_item")
await model.middle.tags.aextend(["tag1", "tag2"])
await model.data.aset_item("count", 42)
```

## Type Validation

### Automatic Type Checking

```python
class TypedModel(BaseRedisModel):
    count: int = 0
    active: bool = True
    tags: List[str] = []

model = TypedModel()

# These will raise TypeError
try:
    await model.count.set("not_a_number")  # ❌ TypeError
    await model.active.set("not_a_bool")   # ❌ TypeError  
    await model.tags.aappend(123)          # ❌ TypeError
except TypeError as e:
    print(f"Type error: {e}")

# These work correctly
await model.count.set(42)           # ✅ int
await model.active.set(False)       # ✅ bool
await model.tags.aappend("valid")   # ✅ str
```

### Custom Validation

Use Pydantic validators for custom validation:

```python
from pydantic import field_validator

class ValidatedModel(BaseRedisModel):
    email: str
    age: int
    tags: List[str] = []
    
    @field_validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v
    
    @field_validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError('Age must be between 0 and 150')
        return v
```

## Serialization Behavior

### Automatic Conversion

RedisPydantic handles serialization automatically:

```python
class MyModel(BaseRedisModel):
    data: bytes = b""
    timestamp: datetime = Field(default_factory=datetime.now)
    config: Dict[str, Any] = {}

model = MyModel()

# Bytes are base64 encoded in Redis
await model.data.set(b"binary_data")

# Complex objects are JSON serialized
await model.config.aset_item("settings", {"theme": "dark", "lang": "en"})

# When loaded back, types are preserved
await model.data.load()     # Returns bytes
await model.config.load()   # Returns Dict[str, Any]
```

### JSON-Compatible Types

For Dict[str, Any] fields, ensure values are JSON-serializable:

```python
class FlexibleModel(BaseRedisModel):
    data: Dict[str, Any] = {}

# These work (JSON-serializable)
await model.data.aupdate(
    name="John",
    age=30,
    active=True,
    scores=[95, 87, 92],
    metadata={"role": "admin"}
)

# These might cause issues (not JSON-serializable)
# await model.data.aset_item("bytes", b"data")            # ❌
```

## Performance Considerations

### Type Overhead

- **Primitive types** (str, int, bool): Minimal overhead
- **Lists and Dicts**: Moderate overhead for serialization
- **Nested models**: Higher overhead due to recursive processing
- **Complex nested types**: Highest overhead

### Optimization Tips

```python
# Good: Use appropriate granularity
class OptimizedModel(BaseRedisModel):
    name: str                    # Fast
    tags: List[str]             # Fast for reasonable sizes
    metadata: Dict[str, str]    # Fast for reasonable sizes

# Less optimal: Over-nested structures
class OverNestedModel(BaseRedisModel):
    data: Dict[str, List[Dict[str, List[str]]]]  # Slower
```

Choose the right balance between structure and performance for your use case.

## Unmapped Types (Pickle Serialization)

Any type not natively supported is automatically handled using pickle serialization. This provides universal compatibility at the cost of some performance and Redis-native operations.

### Examples of Unmapped Types

```python
from typing import Union, Tuple
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
import decimal

# Custom types
Point = namedtuple('Point', ['x', 'y'])

@dataclass  
class Config:
    debug: bool = False
    timeout: float = 30.0

class Status(Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class UniversalModel(BaseRedisModel):
    # These use pickle serialization
    point: Point = Point(0, 0)
    config: Config = Config()
    status: Status = Status.PENDING
    decimal_value: decimal.Decimal = decimal.Decimal('0.00')
    tuple_data: Tuple[int, str, bool] = (1, "test", True)
    union_field: Union[str, int, Point] = "default"
    
    # Any custom class works
    custom_object: Any = None

# Usage is identical to native types
model = UniversalModel()
await model.save()

# Set values
await model.point.set(Point(10, 20))
await model.config.set(Config(debug=True, timeout=60.0))
await model.status.set(Status.COMPLETED)
await model.decimal_value.set(decimal.Decimal('123.45'))

# Load values (types are preserved)
loaded_point = await model.point.load()
assert isinstance(loaded_point, Point)
assert loaded_point.x == 10 and loaded_point.y == 20
```

### Pickle Serialization Behavior

```python
class PickleModel(BaseRedisModel):
    custom_data: Any = None

model = PickleModel()

# Any Python object can be stored
await model.custom_data.set({
    'complex': [1, 2, {'nested': True}],
    'datetime': datetime.now(),
    'decimal': decimal.Decimal('99.99'),
    'function': lambda x: x * 2  # Even functions work
})

# Object is pickled, base64 encoded, and stored in Redis
# When loaded, it's unpickled and original type is restored
loaded_data = await model.custom_data.load()
```

### Considerations for Unmapped Types

**Advantages:**
- Universal compatibility with any Python type
- Automatic type preservation
- No additional configuration required

**Limitations:**
- No Redis-native operations (like atomic increments for numbers)
- Larger storage footprint (pickle + base64 encoding)
- Potential security concerns with unpickling untrusted data
- Not human-readable in Redis
- Performance overhead for serialization/deserialization

**Best Practices:**
- Use native types when possible for better performance
- Reserve unmapped types for complex objects that don't have native equivalents
- Be cautious with pickle serialization in production environments
- Consider JSON serialization for simpler data structures

```python
# Preferred: Use native types when possible
class OptimizedModel(BaseRedisModel):
    count: int = 0                    # Native Redis operations
    tags: List[str] = []             # Native list operations
    metadata: Dict[str, str] = {}    # Native dict operations

# When needed: Use unmapped types for complex objects
class ComplexModel(BaseRedisModel):
    # Native types for simple data
    name: str = ""
    scores: List[int] = []
    
    # Unmapped types for complex objects
    algorithm_state: Any = None      # Custom ML model state
    config_object: ConfigClass = None   # Complex configuration
```

## Quick Reference

### Natively Supported Types
- `str` → RedisStr - String operations
- `int` → RedisInt - Numeric operations with atomic increment
- `bool` → RedisBool - Boolean values  
- `bytes` → RedisBytes - Binary data with base64 encoding
- `datetime` → RedisDatetime - Datetime objects with ISO serialization
- `List[T]` → RedisList - List operations (append, extend, pop, etc.)
- `Dict[K, V]` → RedisDict - Dictionary operations (set, update, pop, etc.)
- Nested Pydantic models → Automatic Redis model conversion

### Universal Support
- **Any other type** → AnyTypeRedis - Pickle serialization
- Examples: `Tuple`, `Union`, `Enum`, `dataclass`, custom classes, `Decimal`, etc.

All types work identically from an API perspective - the difference is in storage efficiency and available operations.