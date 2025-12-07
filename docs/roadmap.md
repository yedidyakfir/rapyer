# Rapyer Roadmap

This is the current roadmap for the rayper package, note that this is just a basic POC.
You are welcome to add suggestions and contribute to our development.

## Bulk Operations Support

**Goal**: Enable efficient bulk insert, update, and delete operations for multiple models

### Tasks
- [ ] **Bulk Insert**: Create multiple models in a single Redis transaction
- [ ] **Bulk Update**: Update multiple models efficiently  
- [ ] **Bulk Delete**: Delete multiple models in one operation
- [ ] **Batch Loading**: Load multiple models by keys efficiently

### Example Usage
```python
# Bulk insert
users = [User(name=f"user{i}") for i in range(100)]
await User.bulk_insert(users)

# Bulk delete
await User.bulk_delete(["user:1", "user:2", "user:3"])

# Batch load
users = await User.bulk_get(["user:1", "user:2", "user:3"])
```

**Benefits**: Better performance for large datasets, reduced Redis round trips

## Complex Selection and Querying

**Goal**: Enable complex field-based queries using Python comparison operators

### Tasks
- [ ] **Field Comparisons**: Support `>`, `<`, `>=`, `<=`, `==`, `!=` operators on model fields
- [ ] **Logical Operators**: Support `&` (and), `|` (or), `~` (not) for complex queries
- [ ] **Query Builder**: Build Redis search queries from Python expressions
- [ ] **Index Management**: Automatic field indexing for query performance

### Example Usage
```python
# Simple field comparisons
adults = await User.find(User.age > 18).to_list()
active_users = await User.find(User.status == "active").to_list()

# Complex queries with logical operators
target_users = await User.find(
    (User.age > 25) & (User.score >= 100) & (User.active == True)
).to_list()

# Single result queries
admin = await User.find_one(User.role == "admin")
```

**Benefits**: Pythonic query syntax, improved developer experience, efficient Redis search

## Conditional Pipeline Actions

**Goal**: Enable complex conditional logic within pipeline operations

### Tasks
- [ ] **Conditional Execution**: Support `if_true()` and `else()` methods on field comparisons
- [ ] **Loop Operations**: Support iteration over collections in pipelines
- [ ] **Nested Conditions**: Allow chaining of conditional statements
- [ ] **Pipeline Context**: Maintain pipeline context through conditional blocks

### Example Usage

```python
async with user.apipeline() as p:
    # Simple conditional
    (p.age > 17).if_true(
        lambda: p.status.set("adult")
    ). else (
        lambda: p.status.set("minor")
    )

    # Complex conditional with multiple actions
    (p.score >= 100).if_true([
        lambda: p.level.set("premium"),
        lambda: p.badges.append("high_scorer"),
        lambda: p.notifications.update({"achievement": "unlocked"})
    ])

    # Loop operations
    for item in p.inventory:
        (item.expired).if_true(
            lambda: p.inventory.remove(item)
        )
```

**Benefits**: Advanced pipeline logic, reduced round trips, atomic conditional operations

## Field Access and Extraction Support

**Goal**: Enable extraction of specific fields from nested structures using dot notation

### Tasks
- [ ] **Nested Field Access**: Support `model.field_lst[0].field_int.get(redis_id)` syntax
- [ ] **Dynamic Field Extraction**: Allow runtime field path resolution
- [ ] **Type Safety**: Maintain type hints through nested access
- [ ] **Performance Optimization**: Efficient Redis operations for nested field access

### Example Usage

```python
# Extract specific nested field
value = await model.field_lst[0].field_int.aget(redis_id)

# Multiple nested field extractions
values = await model.extract_fields([
    "field_lst[0].field_int",
    "field_lst[1].field_str",
    "nested_dict.sub_field"
], redis_id)
```

**Benefits**: Simplified nested data access, improved developer experience, efficient field-specific operations


## TTL Postponement on Model Usage

**Goal**: Allow postponing TTL expiration every time a model is accessed or used, preventing deletion while the model remains active

### Tasks
- [ ] **Usage-Based TTL**: Update TTL automatically when model is accessed or modified
- [ ] **Configurable Behavior**: Option to enable/disable TTL postponement per model class
- [ ] **TTL Refresh Strategy**: Define when and how TTL gets refreshed (read, write, or both)
- [ ] **Performance Optimization**: Efficient TTL updates without impacting model operations
- [ ] **Configuration Options**: Allow setting TTL refresh interval and grace periods

### Example Usage

```python
class User(AtomicRedisModel):
    name: str
    email: str

    class Config:
        ttl_postpone_on_access = True  # Refresh TTL on any access
        ttl_postpone_on_write = True  # Refresh TTL on writes only


# TTL gets postponed automatically
user = await User.get("user:123")  # TTL refreshed to another 3600 seconds
user.name = "Updated Name"  # TTL refreshed again
await user.asave()
```

**Benefits**: Prevents premature deletion of active models, better cache behavior for frequently accessed data, configurable per-model basis

## Unique Data Structure Support

**Goal**: Add support for specialized data structures like priority queues, counters, bloom filters, and other advanced Redis-backed collections

### Tasks
- [ ] **Priority Queue**: Implement Redis-backed priority queue using sorted sets with customizable priority logic
- [ ] **Counter**: Thread-safe counter with atomic increment/decrement operations  
- [ ] **Bloom Filter**: Probabilistic data structure for membership testing
- [ ] **Rate Limiter**: Token bucket or sliding window rate limiting
- [ ] **Circular Buffer**: Fixed-size buffer with automatic overwrite behavior
- [ ] **Type Registry**: System to register and discover custom data structure types
- [ ] **Serialization Strategy**: Pluggable serialization for complex priority/value types

### Example Usage

```python
class TaskQueue(AtomicRedisModel):
    pending_tasks: RedisPriorityQueue[Task, int]  # Task objects with int priority
    request_counter: RedisCounter
    user_filter: RedisBloomFilter[str]  # String membership testing

    class Config:
        priority_queue_order = "min"  # or "max" for max-heap behavior


# Priority queue operations
await queue.pending_tasks.push(task, priority=5)
high_priority_task = await queue.pending_tasks.pop()  # Returns highest priority

# Counter operations  
await queue.request_counter.increment(5)
current_count = await queue.request_counter.aget()

# Bloom filter operations
await queue.user_filter.add("user123")
exists = await queue.user_filter.contains("user123")  # True/False with probability
```

**Benefits**: Support for advanced use cases, better performance for specialized operations, extensible type system for custom data structures

## Lazy and Safe Field Loading

**Goal**: Implement lazy-loading fields that gracefully handle corrupted or unpicklable data without breaking the entire model

### Tasks
- [ ] **Lazy Field Implementation**: Create field types that defer loading until accessed
- [ ] **Safe Loading Mechanism**: Handle corrupted/unpicklable data gracefully without raising errors during model initialization
- [ ] **Error Deferral**: Store loading errors and raise them only when the specific field is accessed
- [ ] **Fallback Strategies**: Configurable fallback values or behaviors for failed field loading
- [ ] **Type Safety**: Maintain type hints and IDE support for lazy fields
- [ ] **Performance Optimization**: Minimize overhead for successfully loaded fields

### Example Usage
```python
class User(AtomicRedisModel):
    name: str
    email: str
    profile_data: LazyField[dict]  # Will not break model if corrupted
    cached_results: SafeField[list, default_factory=list]  # Fallback to empty list
    
    class Config:
        lazy_fields_on_error = "defer"  # or "ignore", "log"

# Model loads successfully even if profile_data is corrupted
user = await User.get("user:123")  # Works even with corrupted pickle data

# Error is raised only when accessing the corrupted field
try:
    profile = user.profile_data  # PickleError raised here, not during model load
except PickleError:
    # Handle corrupted data gracefully
    user.profile_data = {}  # Reset to valid state
```

**Benefits**: Resilient model loading, graceful degradation with corrupted data, partial model functionality when some fields fail to load

## Sync Redis Client Support

**Goal**: Enable synchronous Redis client support alongside the existing async implementation, providing sync equivalents for all operations

### Tasks
- [ ] **Sync Client Implementation**: Add synchronous Redis client wrapper and connection management
- [ ] **Sync Model Operations**: Implement sync versions of core model operations (sync_get, sync_save, sync_delete, etc.)
- [ ] **Sync Pipeline Support**: Enable pipeline operations with synchronous client (sync_pipeline context manager)
- [ ] **Sync Field Operations**: Add synchronous versions for all Redis field types (RedisStr, RedisInt, RedisList, etc.)
- [ ] **Configuration Management**: Support both sync and async clients in model configuration
- [ ] **Testing**: Comprehensive test coverage for all sync operations
- [ ] **Documentation**: Update docs with sync usage patterns and migration guides

### Example Usage
```python
# Sync model operations
user = User.sync_get("user:123")
user.name = "Updated Name"
user.sync_save()

# Sync pipeline operations
with user.sync_pipeline() as p:
    p.score += 10
    p.tags.append("new_tag")
    # All changes applied atomically

# Sync field operations
user.score.sync_update(100)
tags = user.tags.sync_get_all()
```

**Benefits**: Support for synchronous codebases, easier integration with existing sync applications, consistent API patterns between async and sync operations