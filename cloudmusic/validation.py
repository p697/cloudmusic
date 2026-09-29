"""Shared helpers for public input and upstream response validation."""

from .exceptions import ResponseError


def integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("{} 必须是整数".format(name))
    try:
        result = int(value)
    except (ValueError, TypeError):
        raise ValueError("{} 必须是整数".format(name)) from None
    if result < minimum:
        raise ValueError("{} 必须大于或等于 {}".format(name, minimum))
    return result


def ids(value):
    values = value if isinstance(value, (list, tuple)) else [value]
    return [integer(item, "id", 1) for item in values]


def field(data, key, expected_type):
    if not isinstance(data, dict) or not isinstance(data.get(key), expected_type):
        raise ResponseError("网易云响应缺少有效的 {} 字段".format(key))
    return data[key]
