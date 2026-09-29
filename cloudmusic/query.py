"""HTTP handling, deliberately independent of individual music endpoints."""

import requests

from .exceptions import APIError, RequestError, ResponseError


def post(url, headers, data, *, session=None, timeout=(5, 20)):
    if session is None:
        with requests.Session() as owned:
            return post(url, headers, data, session=owned, timeout=timeout)
    try:
        with session.post(url, headers=headers, data=data, timeout=timeout) as response:
            if response.status_code != 200:
                raise RequestError(
                    "网易云 HTTP 请求失败 ({})".format(response.status_code),
                    status_code=response.status_code,
                )
            try:
                result = response.json()
            except ValueError:
                raise ResponseError("网易云返回了无效的 JSON") from None
    except requests.RequestException as exc:
        raise RequestError("网易云网络请求失败或超时") from exc
    if not isinstance(result, dict):
        raise ResponseError("网易云响应不是 JSON 对象")
    if "code" not in result:
        raise ResponseError("网易云响应缺少业务状态码")
    if result["code"] not in (200, "200"):
        message = result.get("message") or result.get("msg") or ""
        raise APIError(result["code"], str(message))
    return result
