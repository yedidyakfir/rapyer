import pytest

from rapyer.types.dct import RedisDict
from rapyer.types.integer import RedisInt
from rapyer.types.lst import RedisList
from rapyer.types.string import RedisStr
from tests.models.collection_types import (
    SimpleListModel,
    SimpleIntListModel,
    SimpleDictModel,
    DictModel,
)
from tests.models.unit_types import (
    SimpleIntDictModel,
    MixedCollectionModel,
    OperationsTestModel,
)
from tests.unit.assertions import (
    assert_redis_dict_item_correct,
    assert_redis_list_correct_types,
    assert_redis_list_item_correct,
)


class TestRedisModelDictOperations:
    @pytest.mark.parametrize(
        ["model1_data", "model2_data", "expected_keys"],
        [
            ({"key1": "value1"}, {"key2": "value2"}, ["key1", "key2"]),
            (
                {"shared": "old"},
                {"shared": "new", "extra": "value"},
                ["shared", "extra"],
            ),
            ({}, {"first": "value"}, ["first"]),
        ],
    )
    def test_dict_update_between_models_sanity(
        self, model1_data, model2_data, expected_keys
    ):
        # Arrange
        model1 = SimpleDictModel(data=model1_data)
        model2 = SimpleDictModel(data=model2_data)

        # Act
        model1.data.update(model2.data)

        # Assert
        assert isinstance(model1.data, RedisDict)
        assert isinstance(model2.data, RedisDict)
        assert set(model1.data.keys()) == set(expected_keys)

        for key in model2_data:
            assert_redis_dict_item_correct(
                model1.data, key, model2_data[key], model1.key, f"data.{key}", RedisStr
            )

        for key in model2_data:
            assert_redis_dict_item_correct(
                model2.data, key, model2_data[key], model2.key, f"data.{key}", RedisStr
            )

    @pytest.mark.parametrize(
        ["model1_counts", "model2_counts", "expected_total"],
        [
            ({"count1": 10}, {"count2": 5}, {"count1": 10, "count2": 5}),
            ({"shared": 3}, {"shared": 7}, {"shared": 7}),
            ({}, {"new": 15}, {"new": 15}),
        ],
    )
    def test_int_dict_update_between_models_sanity(
        self, model1_counts, model2_counts, expected_total
    ):
        # Arrange
        model1 = SimpleIntDictModel(counts=model1_counts)
        model2 = SimpleIntDictModel(counts=model2_counts)

        # Act
        model1.counts.update(model2.counts)

        # Assert
        assert isinstance(model1.counts, RedisDict)
        assert isinstance(model2.counts, RedisDict)

        for key, expected_value in expected_total.items():
            assert int(model1.counts[key]) == expected_value
            assert_redis_dict_item_correct(
                model1.counts,
                key,
                str(expected_value),
                model1.key,
                f"counts.{key}",
                RedisInt,
            )

        for key in model2_counts:
            assert_redis_dict_item_correct(
                model2.counts,
                key,
                str(model2_counts[key]),
                model2.key,
                f"counts.{key}",
                RedisInt,
            )

    def test_dict_or_operator_between_models_sanity(self):
        # Arrange
        model1 = SimpleDictModel(data={"key1": "value1"})
        model2 = SimpleDictModel(data={"key2": "value2", "key3": "value3"})

        # Act
        model1.data |= model2.data

        # Assert
        assert isinstance(model1.data, RedisDict)
        assert isinstance(model2.data, RedisDict)
        assert len(model1.data) == 3
        assert "key1" in model1.data and "key2" in model1.data and "key3" in model1.data

        for key in model2.data:
            assert_redis_dict_item_correct(
                model1.data,
                key,
                str(model2.data[key]),
                model1.key,
                f"data.{key}",
                RedisStr,
            )

        for key in model2.data:
            assert_redis_dict_item_correct(
                model2.data,
                key,
                str(model2.data[key]),
                model2.key,
                f"data.{key}",
                RedisStr,
            )


class TestRedisModelIntegerOperations:
    @pytest.mark.parametrize(
        ["model1_count", "model2_count", "expected_result"],
        [
            (10, 5, 15),
            (0, 1, 1),
            (-5, 10, 5),
        ],
    )
    def test_integer_addition_between_models_sanity(
        self, model1_count, model2_count, expected_result
    ):
        # Arrange
        model1 = OperationsTestModel(int_field=model1_count)
        model2 = OperationsTestModel(int_field=model2_count)

        # Act
        model1.int_field += model2.int_field

        # Assert
        assert isinstance(model1.int_field, RedisInt)
        assert isinstance(model2.int_field, RedisInt)
        assert int(model1.int_field) == expected_result
        assert int(model2.int_field) == model2_count

        assert model1.int_field.key == model1.key
        assert model1.int_field.field_path == "int_field"

        assert model2.int_field.key == model2.key
        assert model2.int_field.field_path == "int_field"

    @pytest.mark.parametrize(
        ["initial_counts", "add_counts"],
        [
            ({"score": 100}, {"bonus": 50}),
            ({"total": 0}, {"increment": 1}),
            ({"base": 25}, {"multiplier": 4}),
        ],
    )
    def test_integer_dict_cross_model_addition_sanity(self, initial_counts, add_counts):
        # Arrange
        model1 = SimpleIntDictModel(counts=initial_counts)
        model2 = SimpleIntDictModel(counts=add_counts)

        model1_key = list(initial_counts.keys())[0]
        model2_key = list(add_counts.keys())[0]

        # Act
        model1.counts[model1_key] += model2.counts[model2_key]

        # Assert
        assert isinstance(model1.counts[model1_key], RedisInt)
        assert isinstance(model2.counts[model2_key], RedisInt)

        expected_result = initial_counts[model1_key] + add_counts[model2_key]
        assert int(model1.counts[model1_key]) == expected_result
        assert int(model2.counts[model2_key]) == add_counts[model2_key]

        assert model1.counts[model1_key].key == model1.key
        assert model1.counts[model1_key].field_path == f"counts.{model1_key}"

        assert model2.counts[model2_key].key == model2.key
        assert model2.counts[model2_key].field_path == f"counts.{model2_key}"


class TestRedisModelListOperations:
    @pytest.mark.parametrize(
        ["model1_items", "model2_items"],
        [
            (["hello"], ["world"]),
            ([], ["first", "second"]),
            (["a", "b"], ["c", "d", "e"]),
        ],
    )
    def test_list_extend_between_models_sanity(self, model1_items, model2_items):
        # Arrange
        model1 = SimpleListModel(items=model1_items)
        model2 = SimpleListModel(items=model2_items)

        # Act
        model1.items.extend(model2.items)

        # Assert
        assert isinstance(model1.items, RedisList)
        assert isinstance(model2.items, RedisList)
        assert len(model1.items) == len(model1_items) + len(model2_items)
        assert len(model2.items) == len(model2_items)

        assert_redis_list_correct_types(model1.items, model1.key, "items", RedisStr)
        assert_redis_list_correct_types(model2.items, model2.key, "items", RedisStr)

    @pytest.mark.parametrize(
        ["model1_items", "model2_items"],
        [
            (["hello"], ["world"]),
            ([], ["first"]),
            (["a"], ["b", "c"]),
        ],
    )
    def test_list_iadd_between_models_sanity(self, model1_items, model2_items):
        # Arrange
        model1 = SimpleListModel(items=model1_items)
        model2 = SimpleListModel(items=model2_items)

        # Act
        model1.items += model2.items

        # Assert
        assert isinstance(model1.items, RedisList)
        assert isinstance(model2.items, RedisList)
        assert len(model1.items) == len(model1_items) + len(model2_items)
        assert len(model2.items) == len(model2_items)

        assert_redis_list_correct_types(model1.items, model1.key, "items", RedisStr)
        assert_redis_list_correct_types(model2.items, model2.key, "items", RedisStr)

    @pytest.mark.parametrize(
        ["model1_numbers", "model2_numbers"],
        [
            ([1, 2], [3, 4]),
            ([10], []),
            ([], [5, 6, 7]),
        ],
    )
    def test_int_list_extend_between_models_sanity(
        self, model1_numbers, model2_numbers
    ):
        # Arrange
        model1 = SimpleIntListModel(numbers=model1_numbers)
        model2 = SimpleIntListModel(numbers=model2_numbers)

        # Act
        model1.numbers.extend(model2.numbers)

        # Assert
        assert isinstance(model1.numbers, RedisList)
        assert isinstance(model2.numbers, RedisList)
        assert len(model1.numbers) == len(model1_numbers) + len(model2_numbers)
        assert len(model2.numbers) == len(model2_numbers)

        for idx, item in enumerate(model1.numbers):
            assert isinstance(item, RedisInt)
            assert item.key == model1.key
            assert item.field_path == f"numbers[{idx}]"

        for idx, item in enumerate(model2.numbers):
            assert isinstance(item, RedisInt)
            assert item.key == model2.key
            assert item.field_path == f"numbers[{idx}]"


class TestRedisModelComplexOperations:
    def test_nested_dict_list_operations_between_models_sanity(self):
        # Arrange
        model1 = MixedCollectionModel(str_list=["hello"], int_dict={"count": 10})
        model2 = MixedCollectionModel(str_list=["world", "test"], int_dict={"score": 5})

        # Act - Add items from model2's list to model1's list
        model1.str_list += model2.str_list

        # Act - Update model1's dict with model2's dict
        model1.int_dict.update(model2.int_dict)

        # Assert list operations
        assert isinstance(model1.str_list, RedisList)
        assert len(model1.str_list) == 3

        assert_redis_list_correct_types(
            model1.str_list, model1.key, "str_list", RedisStr
        )

        # Assert dict operations
        assert isinstance(model1.int_dict, RedisDict)
        assert len(model1.int_dict) == 2
        assert "count" in model1.int_dict and "score" in model1.int_dict

        for key in model1.int_dict:
            assert isinstance(model1.int_dict[key], RedisInt)
            assert_redis_dict_item_correct(
                model1.int_dict,
                key,
                str(model1.int_dict[key]),
                model1.key,
                f"int_dict.{key}",
                RedisInt,
            )

        # Assert model2 remains unchanged
        assert len(model2.str_list) == 2
        assert len(model2.int_dict) == 1

        assert_redis_list_correct_types(
            model2.str_list, model2.key, "str_list", RedisStr
        )

        for key in model2.int_dict:
            assert_redis_dict_item_correct(
                model2.int_dict,
                key,
                str(model2.int_dict[key]),
                model2.key,
                f"int_dict.{key}",
                RedisInt,
            )

    def test_cross_model_nested_access_operations_sanity(self):
        # Arrange
        model1 = MixedCollectionModel(str_dict={"data": "hello"}, int_list=[1, 2, 3])
        model2 = MixedCollectionModel(str_dict={"nested": "world"}, int_list=[10])

        # Act - Complex nested operations
        model1.str_dict.update({"new_key": str(model2.str_dict["nested"])})
        model1.int_list[0] += model2.int_list[0]

        # Assert
        assert isinstance(model1.str_dict, RedisDict)
        assert isinstance(model1.int_list, RedisList)

        assert "new_key" in model1.str_dict
        assert str(model1.str_dict["new_key"]) == "world"
        assert int(model1.int_list[0]) == 11

        assert_redis_dict_item_correct(
            model1.str_dict,
            "new_key",
            "world",
            model1.key,
            "str_dict.new_key",
            RedisStr,
        )

        assert_redis_list_item_correct(
            model1.int_list, 0, "11", model1.key, "int_list[0]", RedisInt
        )

        # Assert model2 remains unchanged
        assert str(model2.str_dict["nested"]) == "world"
        assert int(model2.int_list[0]) == 10

        assert_redis_dict_item_correct(
            model2.str_dict, "nested", "world", model2.key, "str_dict.nested", RedisStr
        )

        assert_redis_list_item_correct(
            model2.int_list, 0, "10", model2.key, "int_list[0]", RedisInt
        )

    @pytest.mark.parametrize(
        ["model1_setup", "model2_setup", "operation_type"],
        [
            (
                {"data": {"inner": "value1"}},
                {"data": {"other": "value2"}},
                "dict_update",
            ),
            ({"data": {"key1": "value1"}}, {"data": {"key2": "value2"}}, "dict_update"),
        ],
    )
    def test_nested_dict_operations_between_models_edge_cases(
        self, model1_setup, model2_setup, operation_type
    ):
        # Arrange
        model1 = DictModel(**model1_setup)
        model2 = DictModel(**model2_setup)

        field_name = list(model1_setup.keys())[0]

        # Act
        if operation_type == "dict_update":
            getattr(model1, field_name).update(getattr(model2, field_name))

        # Assert
        model1_field = getattr(model1, field_name)
        model2_field = getattr(model2, field_name)

        assert isinstance(model1_field, RedisDict)
        assert isinstance(model2_field, RedisDict)

        for key in model1_field:
            assert_redis_dict_item_correct(
                model1_field,
                key,
                str(model1_field[key]),
                model1.key,
                f"{field_name}.{key}",
                RedisStr,
            )

        for key in model2_field:
            assert_redis_dict_item_correct(
                model2_field,
                key,
                str(model2_field[key]),
                model2.key,
                f"{field_name}.{key}",
                RedisStr,
            )
