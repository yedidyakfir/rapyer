import pytest

from rapyer import AtomicRedisModel
from rapyer.base import find_redis_models, REDIS_MODELS


@pytest.fixture
def reset_redis_model_lst():
    original = REDIS_MODELS.copy()
    REDIS_MODELS.clear()
    yield
    REDIS_MODELS.clear()
    REDIS_MODELS.extend(original)


def test_find_redis_models_returns_all_loaded_models_sanity():
    # Arrange
    class Model(AtomicRedisModel):
        field1: int
        field2: str

    class Model2(AtomicRedisModel):
        field1: Model
        field2: type

    # Act
    models = find_redis_models()

    # Assert
    assert models == [Model, Model2]
