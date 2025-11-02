from rapyer.types.dct import RedisDict
from rapyer.types.lst import RedisList


def assert_redis_list_correct_types(
    redis_list: RedisList, key: str, base_path: str, type_check: type = None
):
    assert isinstance(redis_list, RedisList)

    for idx, item in enumerate(redis_list):
        if type_check:
            assert isinstance(redis_list[idx], type_check)
        assert str(redis_list[idx]) == item
        assert redis_list[idx].key == key
        assert redis_list[idx].field_path == f"{base_path}[{idx}]"


def assert_redis_dict_item_correct(
    redis_dict: RedisDict,
    dict_key: str,
    expected_value: str,
    model_key: str,
    field_path: str,
    type_check: type = None,
):
    assert dict_key in redis_dict
    if type_check:
        assert isinstance(redis_dict[dict_key], type_check)
    assert str(redis_dict[dict_key]) == expected_value
    assert redis_dict[dict_key].key == model_key
    assert redis_dict[dict_key].field_path == field_path


def assert_redis_list_item_correct(
    redis_list: RedisList,
    index: int,
    expected_value: str,
    model_key: str,
    field_path: str,
    type_check: type = None,
):
    if type_check:
        assert isinstance(redis_list[index], type_check)
    assert str(redis_list[index]) == expected_value
    assert redis_list[index].key == model_key
    assert redis_list[index].field_path == field_path
