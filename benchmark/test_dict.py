import asyncio
import pytest

from tests.models.collection_types import StrDictModel


@pytest.mark.benchmark
def test__dict_apop__sanity(benchmark, real_redis_client):
    # Arrange
    model = StrDictModel(metadata={"key": "value"})
    loop = asyncio.get_event_loop()
    loop.run_until_complete(model.asave())

    def run_sync():
        return loop.run_until_complete(model.metadata.apop("key"))

    result = benchmark(run_sync)
    assert result == "value"
