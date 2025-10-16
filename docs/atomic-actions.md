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
from rapyer.base import AtomicRedisModel

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
        await pipelined_session.score.set(session.score + level_score)
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
    tags: List[str] = []
    metadata: Dict[str, str] = {}
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
            await pipelined_cart.total_price.set(current_total + (price * quantity))
    
    print(f"Added {len(items_to_add)} items to cart atomically")
```

### Pipeline with Error Handling

```python
async def atomic_user_update(user: User):
    try:
        async with user.pipeline() as pipelined_user:
            await pipelined_user.tags.aappend("verified")
            await pipelined_user.metadata.aupdate(status="active")
            await pipelined_user.profile_views.set(0)  # Reset views
            
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
                await pipelined_queue.processing_tasks.remove(task)
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
                await pipelined_limiter.requests.set(recent_requests)
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
    await pipelined_user.last_login.set(datetime.now())
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
                await pipelined_user.status.set("active")
                await pipelined_user.activated_at.set(datetime.now())
                await pipelined_user.notifications.aappend("Account activated")
```

### 4. Error Handling in Pipelines

```python
async def safe_batch_operation(user: User):
    try:
        async with user.pipeline() as pipelined_user:
            await pipelined_user.tags.aextend(["tag1", "tag2", "tag3"])
            await pipelined_user.metadata.aupdate(batch_processed="true")
            await pipelined_user.last_batch_time.set(datetime.now())
        
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
                    await pipelined_order.status.set("processing")
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
                await order.status.set("out_of_stock")
                return "Order failed - insufficient inventory"
```

This example demonstrates how Rapyer's atomic operations ensure that either:
1. The entire order is processed and inventory is correctly updated, OR
2. Nothing changes if there's insufficient inventory

No partial states or race conditions can occur, even with multiple concurrent order processing attempts.

## Next Steps

Now that you understand atomic actions and concurrency, learn about:

- **[Nested Models](nested-models.md)** - Working with complex nested structures while maintaining atomicity