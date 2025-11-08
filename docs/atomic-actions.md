# Atomic Actions and Concurrency

Rapyer's core strength lies in its atomic operations that prevent race conditions and ensure data consistency in concurrent environments. This guide covers locks, pipelines, and concurrency safety.

## Understanding Atomicity

Traditional Redis operations can lead to race conditions:

```python
# ❌ Race condition prone (traditional approach)
data = await redis.get("user:123:score")
score = int(data) if data else 0
score += 10
await redis.set("user:123:score", score)
# Another process could modify the score between get and set
```

Rapyer eliminates this problem with atomic operations that happen as a single Redis transaction.

## Lock Context Manager

The lock context manager ensures exclusive access to a model during complex operations.

### Basic Locking

```python
from rapyer import AtomicRedisModel

class BankAccount(AtomicRedisModel):
    balance: int = 0
    transaction_count: int = 0
    
async def transfer_money(from_account_key: str, to_account_key: str, amount: int):
    # Lock both accounts to prevent race conditions
    async with BankAccount.lock_from_key(from_account_key, "transfer") as from_account:
        async with BankAccount.lock_from_key(to_account_key, "transfer") as to_account:
            if from_account.balance >= amount:
                from_account.balance -= amount
                from_account.transaction_count += 1
                
                to_account.balance += amount
                to_account.transaction_count += 1
                
                print(f"Transferred ${amount}")
            else:
                print("Insufficient funds")
    # Changes are saved atomically when context exits
```

### Lock Actions

Use action names to allow concurrent operations on different aspects:

```python
from datetime import datetime

class User(AtomicRedisModel):
    name: str
    profile_views: int = 0
    last_login: datetime = None

# These can run concurrently (different actions)
async def update_profile(user_key: str):
    async with User.lock_from_key(user_key, "profile_update") as user:
        user.name = "Updated Name"

async def track_view(user_key: str):
    async with User.lock_from_key(user_key, "view_tracking") as user:
        user.profile_views += 1

# These would be serialized (same action)
async def exclusive_operation(user_key: str):
    async with User.lock_from_key(user_key, "exclusive") as user:
        # Only one of these can run at a time
        pass
```

### Instance Locking

Lock an existing model instance:

```python
async def update_user_safely(user: User):
    async with user.lock("profile_update") as locked_user:
        locked_user.name = "New Name"
        locked_user.profile_views += 1
        # Changes automatically saved when exiting context
```

## Pipeline Operations

Pipelines batch multiple Redis operations into a single atomic transaction, providing both performance benefits and atomicity guarantees.

**Key Concept**: All Redis actions performed on the model (like `aappend`, `aupdate`, `set`) inside a pipeline context are executed as a single atomic action.

### Basic Pipeline Usage

```python
from typing import List, Dict

class GameSession(AtomicRedisModel):
    player_name: str
    score: int = 0
    achievements: List[str] = []
    stats: Dict[str, int] = {}

async def complete_level(session: GameSession, level_score: int, achievement: str):
    # All operations executed atomically as a single transaction
    async with session.pipeline() as pipelined_session:
        session.score += level_score
        await pipelined_session.score.save()
        await pipelined_session.achievements.aappend(achievement)
        await pipelined_session.stats.aupdate(
            levels_completed=session.stats.get("levels_completed", 0) + 1,
            total_time=session.stats.get("total_time", 0) + 120
        )
    # All operations committed together atomically
```

### Pipeline Examples

#### User Registration with Multiple Updates

```python
class User(AtomicRedisModel):
    username: str
    email: str
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = None

async def register_user(username: str, email: str):
    user = User(username=username, email=email, created_at=datetime.now())
    await user.save()
    
    # All profile setup operations happen atomically
    async with user.pipeline() as pipelined_user:
        await pipelined_user.tags.aappend("new_user")
        await pipelined_user.tags.aappend("verified")
        await pipelined_user.metadata.aupdate(
            status="active",
            source="web_registration",
            welcome_email_sent="true"
        )
    
    return user
```

#### Shopping Cart Operations

```python
class ShoppingCart(AtomicRedisModel):
    user_id: str
    items: List[str] = []
    quantities: Dict[str, int] = {}
    total_price: int = 0  # in cents

async def add_multiple_items(cart: ShoppingCart, items_to_add: List[tuple]):
    # Add multiple items atomically to prevent cart corruption
    async with cart.pipeline() as pipelined_cart:
        for item_id, quantity, price in items_to_add:
            await pipelined_cart.items.aappend(item_id)
            await pipelined_cart.quantities.aset_item(item_id, quantity)
            
            # Update total price
            current_total = cart.total_price
            cart.total_price = current_total + (price * quantity)
            await pipelined_cart.total_price.save()
    
    print(f"Added {len(items_to_add)} items to cart atomically")
```

### Pipeline with Error Handling

```python
async def atomic_user_update(user: User):
    try:
        async with user.pipeline() as pipelined_user:
            await pipelined_user.tags.aappend("verified")
            await pipelined_user.metadata.aupdate(status="active")
            user.profile_views = 0  # Reset views
            await pipelined_user.profile_views.save()
            
        print("All updates completed atomically")
        
    except Exception as e:
        print(f"Transaction failed, no changes made: {e}")
        # No partial updates - either all operations succeed or none do
```

### Pipeline Ignore If Deleted

Handle cases where the model might be deleted during pipeline execution:

```python
async def safe_pipeline_update(user: User):
    # If user is deleted during pipeline, operations are ignored
    async with user.pipeline(ignore_if_deleted=True) as pipelined_user:
        await pipelined_user.tags.aappend("updated")
        await pipelined_user.metadata.aset_item("last_update", str(datetime.now()))
    
    # If ignore_if_deleted=False (default), would raise exception if user deleted
```

## Atomic Model Updates with `aupdate()`

The `aupdate()` method provides atomic updates for multiple fields of a BaseModel in a single Redis operation, making it ideal for concurrent environments where partial updates could cause inconsistencies.

### Basic Usage

```python
from rapyer import AtomicRedisModel

class UserProfile(AtomicRedisModel):
    first_name: str
    last_name: str
    email: str
    age: int = 0
    is_verified: bool = False

# Update multiple fields atomically
user = UserProfile(
    first_name="John",
    last_name="Doe", 
    email="john@example.com",
    age=25
)
await user.save()

# Atomic update of multiple fields
await user.aupdate(
    first_name="Jonathan",
    email="jonathan@example.com",
    is_verified=True
)
```

### Concurrency Safety

`aupdate()` ensures that all field updates happen atomically, preventing race conditions:

```python
# ❌ Race condition prone (non-atomic approach)
user.first_name = "Jonathan"
await user.first_name.save()
# Another process could modify the model here
user.email = "jonathan@example.com"
await user.email.save()

# ✅ Atomic approach (race condition safe)
await user.aupdate(
    first_name="Jonathan",
    email="jonathan@example.com"
)
# All changes happen atomically in a single Redis operation
```

### Performance Benefits

`aupdate()` uses Redis JSON path operations to update only the specified fields, providing excellent performance:

```python
class GameCharacter(AtomicRedisModel):
    name: str
    level: int = 1
    experience: int = 0
    health: int = 100
    mana: int = 50
    inventory: Dict[str, int] = {}
    stats: Dict[str, int] = {}

character = GameCharacter(name="Warrior")
await character.save()

# Efficiently update only the fields that changed
await character.aupdate(
    level=15,
    experience=8750,
    health=150
)
# Only these 3 fields are updated in Redis, not the entire model
```

### Type Safety and Validation

`aupdate()` maintains full Pydantic validation and type safety:

```python
class User(AtomicRedisModel):
    username: str
    age: int
    email: str

user = User(username="john", age=25, email="john@example.com")
await user.save()

# ✅ Valid update
await user.aupdate(age=26, email="john.doe@example.com")

# ❌ Type validation error - age must be int
# await user.aupdate(age="twenty-six")  # Pydantic validation error

# ❌ Unknown field error
# await user.aupdate(invalid_field="value")  # Pydantic validation error
```

### Complex Field Updates

`aupdate()` handles all supported Redis types, including complex serialized objects:

```python
from typing import Dict, List, Set
from datetime import datetime

class UserData(AtomicRedisModel):
    preferences: Dict[str, str] = {}
    tags: List[str] = []
    metadata: Dict[str, any] = {}  # Complex serialized data
    last_login: datetime = None

user_data = UserData()
await user_data.save()

# Update complex fields atomically
await user_data.aupdate(
    preferences={"theme": "dark", "language": "en"},
    tags=["premium", "verified"],
    metadata={
        "custom_set": {1, 2, 3},  # Set objects are serialized
        "nested_data": {"key": [1, 2, 3]},
        "custom_type": type(str)  # Type objects are serialized
    },
    last_login=datetime.now()
)
```

### Nested Model Updates

`aupdate()` works with nested AtomicRedisModel instances:

```python
class Address(AtomicRedisModel):
    street: str
    city: str
    country: str = "USA"

class User(AtomicRedisModel):
    name: str
    address: Address

user = User(
    name="John",
    address=Address(street="123 Main St", city="Boston")
)
await user.save()

# Update nested model fields atomically
await user.address.aupdate(
    street="456 Oak Avenue",
    city="Cambridge"
)
# Only the address fields are updated, user.name remains unchanged
```

### Error Handling

`aupdate()` operations are atomic - either all updates succeed or none are applied:

```python
try:
    await user.aupdate(
        valid_field="valid_value",
        invalid_field="invalid_value"  # This field doesn't exist
    )
except ValidationError as e:
    print("Validation failed - no fields were updated")
    # The model state remains unchanged in Redis
```

## Advanced Concurrency Examples

### Task Queue with Atomic Operations

```python
class TaskQueue(AtomicRedisModel):
    pending_tasks: List[str] = []
    processing_tasks: List[str] = []
    completed_tasks: List[str] = []

async def process_next_task(queue_key: str):
    async with TaskQueue.lock_from_key(queue_key, "process_task") as queue:
        if queue.pending_tasks:
            # Move task atomically using pipeline
            async with queue.pipeline() as pipelined_queue:
                task = await queue.pending_tasks.apop(0)  # Remove first task
                await pipelined_queue.processing_tasks.aappend(task)
            
            # Process the task here...
            
            # Mark as completed atomically
            async with queue.pipeline() as pipelined_queue:
                task_index = queue.processing_tasks.index(task)
                await pipelined_queue.processing_tasks.apop(task_index)
                await pipelined_queue.completed_tasks.aappend(task)
            
            return task
    return None
```

### Rate Limiter with Rolling Window

```python
from datetime import datetime, timedelta

class RateLimiter(AtomicRedisModel):
    requests: List[datetime] = []
    limit: int = 100
    window_seconds: int = 3600

async def check_rate_limit(user_id: str) -> bool:
    limiter_key = f"rate_limit:{user_id}"
    
    try:
        limiter = await RateLimiter.get(limiter_key)
    except KeyNotFound:
        limiter = RateLimiter()
        limiter.pk = user_id
        await limiter.save()
    
    now = datetime.now()
    cutoff = now - timedelta(seconds=limiter.window_seconds)
    
    async with limiter.lock("check_limit") as locked_limiter:
        # Clean old requests and add new one atomically
        async with locked_limiter.pipeline() as pipelined_limiter:
            # Filter out old requests
            recent_requests = [req for req in locked_limiter.requests if req > cutoff]
            
            if len(recent_requests) < locked_limiter.limit:
                recent_requests.append(now)
                locked_limiter.requests = recent_requests
                await pipelined_limiter.requests.save()
                return True  # Request allowed
            else:
                return False  # Rate limit exceeded
```

## Pipeline vs Lock Comparison

| Feature | Pipeline | Lock |
|---------|----------|------|
| **Use Case** | Batch multiple operations | Exclusive model access |
| **Performance** | High (batched operations) | Lower (individual operations) |
| **Concurrency** | High (if no conflicts) | Serialized access |
| **Atomicity** | All operations or none | All changes or none |
| **Error Handling** | Transaction rollback | Auto-save on exit |

### When to Use Each

**Use Pipelines when:**
- Performing multiple related operations that should succeed or fail together
- Need maximum performance for batch operations
- Operations don't require reading current values for decisions

```python
# ✅ Good pipeline use case - batch related updates
async with user.pipeline() as pipelined_user:
    await pipelined_user.tags.aappend("verified")
    await pipelined_user.metadata.aupdate(status="active")
    user.last_login = datetime.now()
    await pipelined_user.last_login.save()
```

**Use Locks when:**
- Need to read current values and make decisions based on them
- Complex business logic between operations
- Need to prevent other processes from modifying data during critical operations

```python
# ✅ Good lock use case - conditional logic
async with user.lock("balance_update") as locked_user:
    if locked_user.balance >= withdrawal_amount:
        locked_user.balance -= withdrawal_amount
        locked_user.transaction_count += 1
    else:
        raise InsufficientFundsError()
```

## Best Practices

### 1. Keep Critical Sections Small

```python
# ✅ Good - minimal lock time
async with user.lock("update") as locked_user:
    locked_user.last_seen = datetime.now()

# ❌ Bad - long-running operation in lock
async with user.lock("update") as locked_user:
    data = await external_api_call()  # Blocks other operations
    locked_user.external_data = data
```

### 2. Use Descriptive Action Names

```python
# ✅ Good - clear action names
async with user.lock("profile_update") as locked_user: ...
async with user.lock("password_reset") as locked_user: ...

# ❌ Bad - generic action names
async with user.lock("update") as locked_user: ...
async with user.lock("change") as locked_user: ...
```

### 3. Combine Patterns When Needed

```python
async def complex_user_operation(user: User):
    # Use lock for exclusive access, pipeline for performance within lock
    async with user.lock("complex_update") as locked_user:
        # Read current state and make decisions
        if locked_user.status == "pending":
            # Batch the updates with pipeline for performance
            async with locked_user.pipeline() as pipelined_user:
                locked_user.status = "active"
                await pipelined_user.status.save()
                locked_user.activated_at = datetime.now()
                await pipelined_user.activated_at.save()
                await pipelined_user.notifications.aappend("Account activated")
```

### 4. Error Handling in Pipelines

```python
async def safe_batch_operation(user: User):
    try:
        async with user.pipeline() as pipelined_user:
            await pipelined_user.tags.aextend(["tag1", "tag2", "tag3"])
            await pipelined_user.metadata.aupdate(batch_processed="true")
            user.last_batch_time = datetime.now()
            await pipelined_user.last_batch_time.save()
        
        print("Batch operation completed successfully")
    except Exception as e:
        print(f"Batch operation failed completely: {e}")
        # No partial updates occurred
```

## Complete Example: E-commerce Order Processing

```python
class Order(AtomicRedisModel):
    user_id: str
    items: List[str] = []
    quantities: Dict[str, int] = {}
    total_amount: int = 0
    status: str = "pending"
    payment_attempts: List[datetime] = []

class Inventory(AtomicRedisModel):
    item_quantities: Dict[str, int] = {}
    reserved_items: Dict[str, int] = {}

async def process_order_atomically(order_key: str, inventory_key: str):
    # Lock both order and inventory to prevent race conditions
    async with Order.lock_from_key(order_key, "process") as order:
        async with Inventory.lock_from_key(inventory_key, "reserve") as inventory:
            
            # Check if all items are available
            can_fulfill = True
            for item_id in order.items:
                quantity_needed = order.quantities[item_id]
                available = inventory.item_quantities.get(item_id, 0)
                if available < quantity_needed:
                    can_fulfill = False
                    break
            
            if can_fulfill:
                # Process order and update inventory atomically
                async with order.pipeline() as pipelined_order:
                    order.status = "processing"
                    await pipelined_order.status.save()
                    await pipelined_order.payment_attempts.aappend(datetime.now())
                
                async with inventory.pipeline() as pipelined_inventory:
                    # Reserve items atomically
                    for item_id in order.items:
                        quantity = order.quantities[item_id]
                        current_qty = inventory.item_quantities[item_id]
                        reserved_qty = inventory.reserved_items.get(item_id, 0)
                        
                        await pipelined_inventory.item_quantities.aset_item(
                            item_id, current_qty - quantity
                        )
                        await pipelined_inventory.reserved_items.aset_item(
                            item_id, reserved_qty + quantity
                        )
                
                return "Order processed successfully"
            else:
                order.status = "out_of_stock"
                await order.status.save()
                return "Order failed - insufficient inventory"
```

This example demonstrates how Rapyer's atomic operations ensure that either:
1. The entire order is processed and inventory is correctly updated, OR
2. Nothing changes if there's insufficient inventory

No partial states or race conditions can occur, even with multiple concurrent order processing attempts.

## Next Steps

Now that you understand atomic actions and concurrency, learn about:

- **[Nested Models](nested-models.md)** - Working with complex nested structures while maintaining atomicity