import redis.asyncio as redis_async
from redis import ResponseError
from redis.asyncio.client import Redis
from redis.commands.search.index_definition import IndexDefinition, IndexType

from rapyer.base import REDIS_MODELS


async def init_rapyer(
    redis: str | Redis = None, ttl: int = None, override_old_idx: bool = True
):
    if isinstance(redis, str):
        redis = redis_async.from_url(redis, decode_responses=True, max_connections=20)

    for model in REDIS_MODELS:
        if redis is not None:
            model.Meta.redis = redis
        if ttl is not None:
            model.Meta.ttl = ttl

        # Create indexes for models with indexed fields
        if redis is not None:
            fields = model.redis_schema()
            if fields:

                index_name = f"idx:{model.class_key_initials()}"

                if override_old_idx:
                    try:
                        await redis.ft(index_name).dropindex(delete_documents=False)
                    except ResponseError as e:
                        pass

                await redis.ft(index_name).create_index(
                    fields,
                    definition=IndexDefinition(
                        prefix=[f"{model.class_key_initials()}:"],
                        index_type=IndexType.JSON,
                    ),
                )


async def teardown_rapyer():
    for model in REDIS_MODELS:
        if model.Meta.ttl is not None:
            await model.Meta.redis.aclose()
