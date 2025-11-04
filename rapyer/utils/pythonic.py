import inspect


def safe_issubclass(cls, class_or_tuple):
    return inspect.isclass(cls) and issubclass(cls, class_or_tuple)
