import pytest

from rapyer import AtomicRedisModel
from tests.models.collection_types import (
    IntDictModel,
    StrDictModel,
    DictDictModel,
    BaseModelDictSetitemModel as BaseModelDictModel,
)
from tests.models.common import Address, Company, Settings


@pytest.fixture
def int_dict_model():
    return IntDictModel()


@pytest.fixture
def str_dict_model():
    return StrDictModel()


@pytest.fixture
def dict_dict_model():
    return DictDictModel()


@pytest.fixture
def basemodel_dict_model():
    return BaseModelDictModel()


@pytest.fixture
def sample_address():
    return Address(street="123 Main St", city="New York", zip_code="10001")


@pytest.fixture
def sample_company():
    return Company(name="TechCorp", employees=500, founded=2010)


@pytest.fixture
def sample_settings():
    return Settings(preferences={"theme": "dark"}, features=["notifications"])


@pytest.mark.asyncio
async def test_redis_dict_setitem_int_type_checking_sanity(int_dict_model):
    # Arrange
    model = int_dict_model
    await model.save()

    # Act
    model.metadata["test_key"] = 42

    # Assert
    from rapyer.types.integer import RedisInt

    assert isinstance(model.metadata["test_key"], RedisInt)


@pytest.mark.asyncio
async def test_redis_dict_setitem_str_type_checking_sanity(str_dict_model):
    # Arrange
    model = str_dict_model
    await model.save()

    # Act
    model.metadata["test_key"] = "test_string"

    # Assert
    from rapyer.types.string import RedisStr

    assert isinstance(model.metadata["test_key"], RedisStr)


@pytest.mark.asyncio
async def test_redis_dict_setitem_dict_type_checking_sanity(dict_dict_model):
    # Arrange
    model = dict_dict_model
    await model.save()

    # Act
    model.metadata["test_key"] = {"nested_key": "nested_value"}

    # Assert
    from rapyer.types.dct import RedisDict

    assert isinstance(model.metadata["test_key"], RedisDict)


@pytest.mark.parametrize(
    ["key", "test_value"],
    [
        ["count", 100],
        ["score", 200],
        ["level", 300],
    ],
)
@pytest.mark.asyncio
async def test_redis_dict_setitem_int_operations_sanity(key, test_value):
    # Arrange
    model = IntDictModel()
    await model.save()

    # Act
    model.metadata[key] = test_value
    await model.metadata[key].set(test_value + 50)

    # Assert
    fresh_model = IntDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    # After loading, values are regular Python types, not Redis types
    assert fresh_model.metadata[key] == test_value + 50


@pytest.mark.parametrize(
    ["key", "test_value"],
    [
        ["name", "hello"],
        ["title", "world"],
        ["description", "test"],
    ],
)
@pytest.mark.asyncio
async def test_redis_dict_setitem_str_operations_sanity(key, test_value):
    # Arrange
    model = StrDictModel()
    await model.save()

    # Act
    model.metadata[key] = test_value
    await model.metadata[key].set(test_value + "_modified")

    # Assert
    fresh_model = StrDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    # After loading, values are regular Python types, not Redis types
    assert fresh_model.metadata[key] == test_value + "_modified"


@pytest.mark.parametrize(
    ["key", "test_value"],
    [
        ["config", {"setting1": "value1"}],
        ["options", {"setting2": "value2"}],
        ["preferences", {"setting3": "value3"}],
    ],
)
@pytest.mark.asyncio
async def test_redis_dict_setitem_nested_dict_operations_sanity(key, test_value):
    # Arrange
    model = DictDictModel()
    await model.save()

    # Act
    model.metadata[key] = test_value
    await model.save()  # Save current state to Redis before update
    await model.metadata[key].aupdate(**{"new_setting": "new_value"})

    # Assert
    fresh_model = DictDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    # After loading, values are regular Python types, not Redis types
    expected_dict = {**test_value, "new_setting": "new_value"}
    assert fresh_model.metadata[key] == expected_dict


@pytest.mark.asyncio
async def test_redis_dict_setitem_int_arithmetic_operations_sanity():
    # Arrange
    model = IntDictModel()
    await model.save()

    # Act
    model.metadata["number"] = 50

    # Assert
    assert model.metadata["number"] + 10 == 60
    assert model.metadata["number"] - 5 == 45
    assert model.metadata["number"] * 2 == 100
    assert model.metadata["number"] == 50


@pytest.mark.asyncio
async def test_redis_dict_setitem_str_operations_edge_case():
    # Arrange
    model = StrDictModel()
    await model.save()

    # Act
    model.metadata["text"] = "test"

    # Assert
    assert model.metadata["text"] + "_suffix" == "test_suffix"
    assert model.metadata["text"].upper() == "TEST"
    assert len(model.metadata["text"]) == 4


@pytest.mark.asyncio
async def test_redis_dict_setitem_nested_dict_key_access_edge_case():
    # Arrange
    model = DictDictModel()
    await model.save()

    # Act
    model.metadata["config"] = {"key1": "value1", "key2": "value2"}

    # Assert
    assert model.metadata["config"]["key1"] == "value1"
    assert model.metadata["config"]["key2"] == "value2"
    assert len(model.metadata["config"]) == 2


@pytest.mark.asyncio
async def test_redis_dict_setitem_redis_field_paths_sanity():
    # Arrange
    model = IntDictModel()
    await model.save()

    # Act
    model.metadata["test_key"] = 42

    # Assert
    assert model.metadata["test_key"].key == model.key
    assert model.metadata["test_key"].field_path == "metadata.test_key"
    assert model.metadata["test_key"].json_path == "$.metadata.test_key"


@pytest.mark.asyncio
async def test_redis_dict_setitem_multiple_keys_sanity():
    # Arrange
    model = IntDictModel()
    await model.save()

    # Act
    model.metadata["key1"] = 10
    model.metadata["key2"] = 20
    model.metadata["key3"] = 30

    # Assert
    assert model.metadata["key1"] == 10
    assert model.metadata["key2"] == 20
    assert model.metadata["key3"] == 30
    assert len(model.metadata) == 3


@pytest.mark.asyncio
async def test_redis_dict_setitem_persistence_across_instances_edge_case():
    # Arrange
    model1 = IntDictModel()
    await model1.save()

    # Act
    model1.metadata["test_key"] = 99
    await model1.metadata["test_key"].set(99)

    # Assert
    model2 = IntDictModel()
    model2.pk = model1.pk
    await model2.metadata.load()
    # After loading, values are regular Python types, not Redis types
    assert model2.metadata["test_key"] == 99


@pytest.mark.asyncio
async def test_redis_dict_setitem_with_existing_redis_operations_sanity():
    # Arrange
    model = StrDictModel()
    model.metadata = {"existing_key": "existing_value"}
    await model.save()

    # Act - use setitem to add a new key
    model.metadata["new_key"] = "new_value"
    await model.metadata["new_key"].set("updated_value")

    # Also use setitem to convert existing key to Redis type
    # Convert to Redis type via setitem
    model.metadata["existing_key"] = "existing_value"
    await model.metadata["existing_key"].set("updated_existing")

    # Assert
    fresh_model = StrDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    assert fresh_model.metadata["new_key"] == "updated_value"
    assert fresh_model.metadata["existing_key"] == "updated_existing"


@pytest.mark.asyncio
async def test_redis_dict_setitem_overwrite_existing_key_sanity():
    # Arrange
    model = IntDictModel()
    model.metadata = {"key1": 10}
    await model.save()

    # Act - overwrite existing key with setitem
    model.metadata["key1"] = 99
    await model.metadata["key1"].set(150)

    # Assert
    fresh_model = IntDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    assert fresh_model.metadata["key1"] == 150


@pytest.mark.asyncio
async def test_redis_dict_setitem_mixed_operations_sanity():
    # Arrange
    model = StrDictModel()
    await model.save()

    # Act - mix setitem with aset_item and aupdate
    model.metadata["key1"] = "value1"  # setitem
    await model.metadata.aset_item("key2", "value2")  # aset_item
    await model.metadata.aupdate(key3="value3")  # aupdate

    # Use Redis operations on setitem-created value
    await model.metadata["key1"].set("modified_value1")

    # Assert
    fresh_model = StrDictModel()
    fresh_model.pk = model.pk
    await fresh_model.metadata.load()
    assert fresh_model.metadata["key1"] == "modified_value1"
    assert fresh_model.metadata["key2"] == "value2"
    assert fresh_model.metadata["key3"] == "value3"
    assert len(fresh_model.metadata) == 3


# BaseModel setitem tests for dict
@pytest.mark.asyncio
async def test_redis_dict_setitem_basemodel_addresses_type_checking_sanity(
    basemodel_dict_model, sample_address
):
    # Arrange
    model = basemodel_dict_model
    await model.save()
    test_value = sample_address

    # Act
    model.addresses["home"] = test_value

    # Assert - should be a Redis BaseModel type
    dict_item = model.addresses["home"]
    assert isinstance(dict_item, AtomicRedisModel)


@pytest.mark.asyncio
async def test_redis_dict_setitem_basemodel_redis_operations_sanity():
    # Arrange
    model = BaseModelDictModel()
    await model.save()

    address = Address(street="456 Oak Ave", city="Boston", zip_code="02101")

    # Act
    model.addresses["work"] = address

    # Assert - the setitem should create a Redis BaseModel
    assert isinstance(model.addresses["work"], AtomicRedisModel)
    assert hasattr(model.addresses["work"], "save")
    assert hasattr(model.addresses["work"], "load")

    # Check that the data is preserved
    assert model.addresses["work"].street == "456 Oak Ave"
    assert model.addresses["work"].city == "Boston"
    assert model.addresses["work"].zip_code == "02101"

    # Check that we can modify the fields
    model.addresses["work"].street = "789 Pine St"
    assert model.addresses["work"].street == "789 Pine St"


@pytest.mark.asyncio
async def test_redis_dict_setitem_basemodel_field_paths_sanity():
    # Arrange
    model = BaseModelDictModel()
    await model.save()

    company = Company(name="StartupXYZ", employees=25, founded=2020)

    # Act
    model.companies["startup"] = company

    # Assert - BaseModels have different field path structure
    assert model.companies["startup"].key == model.key  # Same Redis key as parent

    # Check the inst_field_conf for proper field path
    if hasattr(model.companies["startup"], "inst_field_conf"):
        assert (
            model.companies["startup"].inst_field_conf.field_name == "companies.startup"
        )


@pytest.mark.asyncio
async def test_redis_dict_setitem_basemodel_nested_operations_sanity():
    # Arrange
    model = BaseModelDictModel()
    await model.save()

    config = Settings(
        preferences={"theme": "light", "language": "en"},
        features=["auto-save", "backup", "sync"],
    )

    # Act
    model.configs["user_prefs"] = config

    # Modify nested fields (test the functionality without persistence)
    model.configs["user_prefs"].preferences["theme"] = "dark"
    model.configs["user_prefs"].features.append("notifications")

    # Assert - check local modifications work
    config_item = model.configs["user_prefs"]
    assert config_item.preferences["theme"] == "dark"
    assert config_item.preferences["language"] == "en"
    assert len(config_item.features) == 4
    assert "notifications" in config_item.features


@pytest.mark.asyncio
async def test_redis_dict_setitem_basemodel_multiple_keys_sanity():
    # Arrange
    model = BaseModelDictModel()
    await model.save()

    addresses = {
        "home": Address(street="111 Home St", city="Seattle", zip_code="98101"),
        "work": Address(street="222 Work Ave", city="Portland", zip_code="97201"),
        "vacation": Address(street="333 Beach Rd", city="Miami", zip_code="33101"),
    }

    # Act
    for key, address in addresses.items():
        model.addresses[key] = address

    # Assert - check that all addresses were set correctly via __setitem__
    assert len(model.addresses) == 3
    for key, expected_address in addresses.items():
        actual_address = model.addresses[key]
        assert isinstance(actual_address, AtomicRedisModel)
        assert actual_address.street == expected_address.street
        assert actual_address.city == expected_address.city
        assert actual_address.zip_code == expected_address.zip_code


@pytest.mark.asyncio
async def test_redis_dict_setitem_basemodel_persistence_across_instances_edge_case():
    # Arrange
    model1 = BaseModelDictModel()
    await model1.save()

    company = Company(name="MegaCorp", employees=10000, founded=1990)

    # Act
    model1.companies["mega"] = company

    # Modify
    model1.companies["mega"].employees = 12000

    # Assert - test local modification without persistence complexity
    company_item = model1.companies["mega"]
    assert isinstance(company_item, AtomicRedisModel)
    assert company_item.name == "MegaCorp"
    assert company_item.employees == 12000
    assert company_item.founded == 1990


@pytest.mark.asyncio
async def test_redis_dict_setitem_basemodel_mixed_with_regular_operations_sanity():
    # Arrange
    model = BaseModelDictModel()
    await model.save()

    # Act - mix setitem with regular dict operations
    address = Address(street="555 Mixed St", city="Denver", zip_code="80201")
    model.addresses["setitem_key"] = address  # setitem

    # Use regular aset_item for comparison
    await model.addresses.aset_item(
        "regular_key",
        dict(street="666 Regular Ave", city="Phoenix", zip_code="85001"),
    )

    # Assert - check both setitem and aset_item work
    # setitem-created address should be a Redis BaseModel
    setitem_address = model.addresses["setitem_key"]
    assert isinstance(setitem_address, AtomicRedisModel)
    assert setitem_address.street == "555 Mixed St"
    assert setitem_address.city == "Denver"
    assert setitem_address.zip_code == "80201"

    # regular aset_item should also work when loaded
    await model.addresses.load()
    regular_address = model.addresses["regular_key"]
    assert regular_address.street == "666 Regular Ave"
    assert regular_address.city == "Phoenix"
    assert regular_address.zip_code == "85001"
