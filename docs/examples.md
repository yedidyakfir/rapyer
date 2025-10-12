# Examples

Real-world examples showing how to use RedisPydantic in different scenarios.

## User Session Management

```python
import asyncio
from datetime import datetime
from redis_pydantic.base import BaseRedisModel
from typing import List, Dict

class UserSession(BaseRedisModel):
    user_id: str
    session_data: Dict[str, str] = {}
    activity_log: List[str] = []
    is_active: bool = True
    last_seen: str = ""
    login_count: int = 0

async def session_example():
    # Create new session
    session = UserSession(user_id="user123")
    await session.save()
    
    # Track user login
    await session.activity_log.aappend(f"login:{datetime.now().isoformat()}")
    await session.session_data.aupdate(
        ip_address="192.168.1.1",
        user_agent="Chrome/91.0",
        device="desktop"
    )
    await session.login_count.set(1)
    
    # Update activity
    await session.activity_log.aappend(f"page_view:/dashboard:{datetime.now().isoformat()}")
    await session.last_seen.set(datetime.now().isoformat())
    
    # Track logout
    await session.is_active.set(False)
    await session.activity_log.aappend(f"logout:{datetime.now().isoformat()}")
    
    print(f"Session {session.key} for user {session.user_id}")
    print(f"Activity log: {session.activity_log}")
    print(f"Session data: {session.session_data}")

if __name__ == "__main__":
    asyncio.run(session_example())
```

## E-commerce Shopping Cart

```python
import asyncio
from redis_pydantic.base import BaseRedisModel
from typing import List, Dict
from pydantic import BaseModel, Field

class CartItem(BaseModel):
    product_id: str
    name: str
    price: int  # in cents
    quantity: int = 1

class ShoppingCart(BaseRedisModel):
    user_id: str
    items: List[str] = []  # product IDs
    quantities: Dict[str, int] = {}
    prices: Dict[str, int] = {}  # product_id -> price in cents
    total_amount: int = 0
    discount_codes: List[str] = []
    metadata: Dict[str, str] = {}

async def cart_example():
    # Create shopping cart
    cart = ShoppingCart(user_id="user456")
    await cart.save()
    
    # Add items to cart
    products = [
        {"id": "prod123", "name": "Python Book", "price": 2999},
        {"id": "prod456", "name": "Redis Guide", "price": 1999},
    ]
    
    for product in products:
        await cart.items.aappend(product["id"])
        await cart.quantities.aset_item(product["id"], 1)
        await cart.prices.aset_item(product["id"], product["price"])
    
    # Update quantity
    await cart.quantities.aset_item("prod123", 2)
    
    # Calculate total
    total = 0
    for item_id in cart.items:
        quantity = cart.quantities.get(item_id, 0)
        price = cart.prices.get(item_id, 0)
        total += quantity * price
    
    await cart.total_amount.set(total)
    
    # Apply discount
    await cart.discount_codes.aappend("SAVE10")
    await cart.metadata.aset_item("discount_applied", "true")
    await cart.metadata.aset_item("original_total", str(total))
    
    discounted_total = int(total * 0.9)  # 10% discount
    await cart.total_amount.set(discounted_total)
    
    print(f"Cart {cart.key} for user {cart.user_id}")
    print(f"Items: {cart.items}")
    print(f"Quantities: {cart.quantities}")
    print(f"Total: ${cart.total_amount / 100:.2f}")
    print(f"Discount codes: {cart.discount_codes}")

if __name__ == "__main__":
    asyncio.run(cart_example())
```

## Application Configuration

```python
import asyncio
from redis_pydantic.base import BaseRedisModel
from typing import Dict, List
from pydantic import BaseModel, Field

class FeatureFlags(BaseModel):
    new_ui: bool = False
    beta_features: bool = False
    advanced_analytics: bool = False

class RateLimits(BaseModel):
    requests_per_minute: int = 1000
    max_file_size: int = 10485760  # 10MB
    concurrent_connections: int = 100

class AppConfig(BaseRedisModel):
    features: Dict[str, bool] = {}
    limits: Dict[str, int] = {}
    allowed_ips: List[str] = []
    blocked_ips: List[str] = []
    maintenance_mode: bool = False
    version: str = "1.0.0"

async def config_example():
    # Create application config
    config = AppConfig()
    await config.save()
    
    # Configure feature flags
    await config.features.aupdate(
        new_ui=True,
        beta_features=False,
        advanced_analytics=True,
        dark_mode=True
    )
    
    # Set rate limits
    await config.limits.aupdate(
        requests_per_minute=1000,
        max_file_size=10485760,
        concurrent_connections=100,
        max_upload_size=52428800  # 50MB
    )
    
    # Manage IP lists
    await config.allowed_ips.aextend([
        "192.168.1.0/24",
        "10.0.0.0/8",
        "172.16.0.0/12"
    ])
    
    await config.blocked_ips.aappend("192.168.1.100")
    
    # Update version
    await config.version.set("1.1.0")
    
    # Enable maintenance mode temporarily
    await config.maintenance_mode.set(True)
    
    # Simulate config reload
    print("Current configuration:")
    print(f"Features: {config.features}")
    print(f"Limits: {config.limits}")
    print(f"Allowed IPs: {config.allowed_ips}")
    print(f"Maintenance mode: {config.maintenance_mode}")
    print(f"Version: {config.version}")
    
    # Disable maintenance mode
    await config.maintenance_mode.set(False)

if __name__ == "__main__":
    asyncio.run(config_example())
```

## Real-time Analytics

```python
import asyncio
from datetime import datetime, timedelta
from redis_pydantic.base import BaseRedisModel
from typing import Dict, List

class AnalyticsData(BaseRedisModel):
    page_views: Dict[str, int] = {}
    user_actions: List[str] = []
    daily_stats: Dict[str, int] = {}
    hourly_stats: Dict[str, int] = {}
    top_pages: List[str] = []
    error_count: int = 0
    last_updated: str = ""

async def analytics_example():
    # Create analytics instance
    analytics = AnalyticsData()
    await analytics.save()
    
    # Track page views
    pages = ["/home", "/products", "/about", "/contact", "/home", "/products", "/home"]
    
    for page in pages:
        current_count = analytics.page_views.get(page, 0)
        await analytics.page_views.aset_item(page, current_count + 1)
    
    # Track user actions
    actions = [
        f"user_login:user123:{datetime.now().isoformat()}",
        f"page_view:/home:user123:{datetime.now().isoformat()}",
        f"button_click:subscribe:user123:{datetime.now().isoformat()}",
        f"form_submit:contact:user123:{datetime.now().isoformat()}"
    ]
    
    await analytics.user_actions.aextend(actions)
    
    # Update daily stats
    today = datetime.now().strftime("%Y-%m-%d")
    await analytics.daily_stats.aupdate(
        total_views=len(pages),
        unique_visitors=1,
        new_signups=0,
        conversions=1
    )
    
    # Update hourly stats
    current_hour = datetime.now().strftime("%Y-%m-%d-%H")
    await analytics.hourly_stats.aset_item(current_hour, len(pages))
    
    # Calculate top pages
    sorted_pages = sorted(analytics.page_views.items(), key=lambda x: x[1], reverse=True)
    top_pages = [page for page, _ in sorted_pages[:5]]
    await analytics.top_pages.aclear()
    await analytics.top_pages.aextend(top_pages)
    
    # Update timestamp
    await analytics.last_updated.set(datetime.now().isoformat())
    
    print("Analytics Dashboard:")
    print(f"Page views: {analytics.page_views}")
    print(f"Top pages: {analytics.top_pages}")
    print(f"Daily stats: {analytics.daily_stats}")
    print(f"Total actions tracked: {len(analytics.user_actions)}")
    print(f"Last updated: {analytics.last_updated}")

if __name__ == "__main__":
    asyncio.run(analytics_example())
```

## Chat Application

```python
import asyncio
from datetime import datetime
from redis_pydantic.base import BaseRedisModel
from typing import List, Dict
from pydantic import BaseModel, Field

class Message(BaseModel):
    id: str
    user_id: str
    content: str
    timestamp: str
    message_type: str = "text"  # text, image, file

class ChatRoom(BaseRedisModel):
    room_id: str
    name: str
    participants: List[str] = []
    messages: List[str] = []  # message IDs
    active_users: List[str] = []
    metadata: Dict[str, str] = {}
    created_at: str = ""
    message_count: int = 0

class UserPresence(BaseRedisModel):
    user_id: str
    online: bool = False
    last_seen: str = ""
    current_rooms: List[str] = []
    status_message: str = ""

async def chat_example():
    # Create chat room
    room = ChatRoom(
        room_id="general",
        name="General Discussion",
        created_at=datetime.now().isoformat()
    )
    await room.save()
    
    # Create user presence
    user1 = UserPresence(user_id="user123")
    user2 = UserPresence(user_id="user456")
    await user1.save()
    await user2.save()
    
    # Users join room
    await room.participants.aextend(["user123", "user456"])
    await room.active_users.aextend(["user123", "user456"])
    
    await user1.online.set(True)
    await user1.current_rooms.aappend("general")
    await user1.status_message.set("Working on RedisPydantic")
    
    await user2.online.set(True)
    await user2.current_rooms.aappend("general")
    
    # Simulate messages
    messages = [
        {"id": "msg1", "user": "user123", "content": "Hello everyone!"},
        {"id": "msg2", "user": "user456", "content": "Hi there! How's it going?"},
        {"id": "msg3", "user": "user123", "content": "Working on some Redis stuff"},
    ]
    
    for msg in messages:
        await room.messages.aappend(msg["id"])
        await room.message_count.set(room.message_count + 1)
    
    # Update room metadata
    await room.metadata.aupdate(
        last_activity=datetime.now().isoformat(),
        most_active_user="user123",
        topic="Redis and Python discussion"
    )
    
    # User leaves
    await room.active_users.apop()  # Remove last user
    await user2.online.set(False)
    await user2.last_seen.set(datetime.now().isoformat())
    
    print(f"Chat room: {room.name}")
    print(f"Participants: {room.participants}")
    print(f"Active users: {room.active_users}")
    print(f"Message count: {room.message_count}")
    print(f"Room metadata: {room.metadata}")
    print(f"User1 status: {user1.status_message}")

if __name__ == "__main__":
    asyncio.run(chat_example())
```

## Task Queue with Status Tracking

```python
import asyncio
from datetime import datetime
from redis_pydantic.base import BaseRedisModel
from typing import List, Dict, Optional
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(BaseRedisModel):
    task_id: str
    name: str
    status: str = TaskStatus.PENDING
    progress: int = 0
    result: str = ""
    error_message: str = ""
    logs: List[str] = []
    metadata: Dict[str, str] = {}
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""

class TaskQueue(BaseRedisModel):
    queue_name: str
    pending_tasks: List[str] = []
    running_tasks: List[str] = []
    completed_tasks: List[str] = []
    failed_tasks: List[str] = []
    stats: Dict[str, int] = {}

async def task_queue_example():
    # Create task queue
    queue = TaskQueue(queue_name="data_processing")
    await queue.save()
    
    # Initialize stats
    await queue.stats.aupdate(
        total_tasks=0,
        completed=0,
        failed=0,
        running=0
    )
    
    # Create tasks
    tasks = [
        {"id": "task1", "name": "Process CSV file"},
        {"id": "task2", "name": "Generate report"},
        {"id": "task3", "name": "Send notifications"},
    ]
    
    task_objects = []
    for task_data in tasks:
        task = Task(
            task_id=task_data["id"],
            name=task_data["name"],
            created_at=datetime.now().isoformat()
        )
        await task.save()
        task_objects.append(task)
        
        # Add to queue
        await queue.pending_tasks.aappend(task.task_id)
        current_total = queue.stats.get("total_tasks", 0)
        await queue.stats.aset_item("total_tasks", current_total + 1)
    
    # Process first task
    task1 = task_objects[0]
    
    # Move to running
    await queue.pending_tasks.apop(0)  # Remove from pending
    await queue.running_tasks.aappend(task1.task_id)
    
    # Update task status
    await task1.status.set(TaskStatus.RUNNING)
    await task1.started_at.set(datetime.now().isoformat())
    await task1.logs.aappend(f"Task started at {datetime.now().isoformat()}")
    
    # Simulate progress
    for progress in [25, 50, 75, 100]:
        await task1.progress.set(progress)
        await task1.logs.aappend(f"Progress: {progress}%")
        await asyncio.sleep(0.1)  # Simulate work
    
    # Complete task
    await task1.status.set(TaskStatus.COMPLETED)
    await task1.completed_at.set(datetime.now().isoformat())
    await task1.result.set("CSV processed successfully, 1000 records")
    await task1.logs.aappend("Task completed successfully")
    
    # Move to completed
    await queue.running_tasks.apop()  # Remove from running
    await queue.completed_tasks.aappend(task1.task_id)
    
    # Update queue stats
    current_completed = queue.stats.get("completed", 0)
    await queue.stats.aset_item("completed", current_completed + 1)
    
    # Simulate task failure
    task2 = task_objects[1]
    await queue.pending_tasks.apop(0)  # Remove from pending
    await queue.running_tasks.aappend(task2.task_id)
    
    await task2.status.set(TaskStatus.RUNNING)
    await task2.started_at.set(datetime.now().isoformat())
    await task2.progress.set(30)
    
    # Fail the task
    await task2.status.set(TaskStatus.FAILED)
    await task2.error_message.set("Database connection failed")
    await task2.logs.aextend([
        "Started report generation",
        "Connecting to database...",
        "ERROR: Database connection timeout"
    ])
    
    # Move to failed
    await queue.running_tasks.apop()
    await queue.failed_tasks.aappend(task2.task_id)
    
    current_failed = queue.stats.get("failed", 0)
    await queue.stats.aset_item("failed", current_failed + 1)
    
    print("Task Queue Status:")
    print(f"Pending: {queue.pending_tasks}")
    print(f"Running: {queue.running_tasks}")
    print(f"Completed: {queue.completed_tasks}")
    print(f"Failed: {queue.failed_tasks}")
    print(f"Stats: {queue.stats}")
    
    print(f"\nTask 1 Details:")
    print(f"Status: {task1.status}")
    print(f"Progress: {task1.progress}%")
    print(f"Result: {task1.result}")
    print(f"Logs: {task1.logs}")
    
    print(f"\nTask 2 Details:")
    print(f"Status: {task2.status}")
    print(f"Error: {task2.error_message}")
    print(f"Logs: {task2.logs}")

if __name__ == "__main__":
    asyncio.run(task_queue_example())
```

## Running the Examples

Each example is self-contained and can be run independently:

```bash
# Make sure Redis is running
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest

# Run any example
python session_example.py
python cart_example.py
python config_example.py
python analytics_example.py
python chat_example.py
python task_queue_example.py
```

These examples demonstrate:

- **Session Management**: User tracking, activity logging, session data
- **E-commerce**: Shopping cart, inventory, pricing, discounts
- **Configuration**: Feature flags, rate limits, IP management
- **Analytics**: Real-time data tracking, statistics, dashboards
- **Chat**: Real-time messaging, user presence, room management
- **Task Processing**: Background jobs, progress tracking, queue management

Each pattern shows best practices for using RedisPydantic in production applications.