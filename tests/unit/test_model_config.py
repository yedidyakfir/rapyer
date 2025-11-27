from rapyer.types import RedisInt, RedisList
from tests.models.specialized import ModelWithConfig


def test__model_config__create_model_with_config_override__sanity():
    # Act
    model = ModelWithConfig()

    # Assert
    ModelWithConfig.model_config["validate_default"] = True
    ModelWithConfig.model_config["validate_assignment"] = True

    assert isinstance(model.int_field, RedisInt)
    assert isinstance(model.tags, RedisList)
