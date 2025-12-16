import asyncio

import pytest

from tests.models.collection_types import StrDictModel


@pytest.mark.benchmark
def test__dict_apop__sanity(benchmark, real_redis_client):
    # Arrange
    model = StrDictModel(metadata={"key": "value"})

    def run_sync():
        return asyncio.run(model.metadata.apop()())

    result = benchmark(run_sync)
    assert result == "value"
