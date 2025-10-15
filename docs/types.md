# Supported Types

RedisPydantic supports various Python types with automatic Redis serialization and type validation.

## Primitive Types

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