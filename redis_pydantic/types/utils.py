async def noop():
    return


def update_keys_in_pipeline(pipeline, redis_key: str, **kwargs):
    for key, value in kwargs.items():
        pipeline.json().set(redis_key, key, value)