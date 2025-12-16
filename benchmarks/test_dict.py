import asyncio
import pytest

from tests.models.collection_types import StrDictModel


@pytest.mark.benchmark
def test__dict_apop__sanity(benchmark, real_redis_client):
    # Arrange
    loop = asyncio.get_event_loop()

    def setup():
        model = StrDictModel(metadata={"key": "value"})
        loop.run_until_complete(model.asave())
        return (model,), {}

    def run_sync(model):
        return loop.run_until_complete(model.metadata.apop("key"))

    # Act
    result = benchmark.pedantic(run_sync, setup=setup, rounds=20)
    assert result == "value"
