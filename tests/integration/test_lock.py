import asyncio

from redis.asyncio import Redis

from rapyer.utils.redis import acquire_lock


async def worker(redis: Redis, name: str, work_duration: float):
    print(f"[{name}] Trying to acquire lock...")

    async with acquire_lock(redis, "my-resource") as token:
        print(f"[{name}] ✅ Acquired lock (token: {token[:8]})")

        # Simulate work
        for i in range(int(work_duration)):
            # Check if we still own the lock
            current_token = await redis.get("my-resource:lock")
            if current_token is None:
                print(f"[{name}] ⚠️  Second {i}: Lock EXPIRED (key gone)")
            elif current_token.decode() != token:
                print(f"[{name}] 🔴 Second {i}: SOMEONE ELSE owns the lock now!")
            else:
                print(f"[{name}] Second {i}: Still holding lock")
            await asyncio.sleep(1)

        print(f"[{name}] Finished work, releasing lock...")

    print(f"[{name}] Exited context manager")


async def main():
    redis = Redis(host="localhost", port=6379, decode_responses=False)
    await redis.delete("my-resource:lock")  # Clean start

    # Client A: takes 8 seconds but lock expires in 5
    # Client B: starts at T=3, waits for lock, gets it when A's expires
    await asyncio.gather(
        worker(redis, "Client-A", work_duration=8),
        delayed_worker(redis, "Client-B", delay=3, work_duration=6),
    )

    await redis.aclose()


async def delayed_worker(redis: Redis, name: str, delay: float, work_duration: float):
    await asyncio.sleep(delay)
    await worker(redis, name, work_duration)


if __name__ == "__main__":
    asyncio.run(main())
