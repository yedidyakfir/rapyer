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
