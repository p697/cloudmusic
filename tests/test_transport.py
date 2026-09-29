import base64
import json
from unittest.mock import MagicMock

import pytest
import requests
from Cryptodome.Cipher import AES

from cloudmusic import APIError, RequestError, ResponseError
from cloudmusic import encrypt, query
from cloudmusic.api import Api


def response(payload=None, status=200):
    value = MagicMock(status_code=status)
    value.__enter__.return_value = value
    value.json.return_value = payload
    return value


def test_json_encryption_unicode_quotes_and_types(monkeypatch):
    secret = b"0123456789abcdef"
    monkeypatch.setattr(encrypt, "create_key", lambda _: secret)
    payload = {"s": '白日 "hello" \\ path', "ids": [1], "flag": True, "nothing": None}
    encrypted = encrypt.encrypted_request(payload)

    def decrypt(value, key):
        plain = AES.new(key, AES.MODE_CBC, b"0102030405060708").decrypt(base64.b64decode(value))
        return plain[: -plain[-1]]

    assert json.loads(decrypt(decrypt(encrypted["params"], secret), encrypt.NONCE)) == payload
    assert len(encrypted["encSecKey"]) == 256
    assert len(encrypt.create_key(16)) == 16
    assert encrypt.encrypted_request(payload, "linux") is payload
    assert encrypt.linuxEncrypt() == {}
    assert encrypt.encrypted_request() and encrypt.encrypted_request('{"id":1}')


def test_query_success_and_closes_response():
    reply = response({"code": 200, "songs": []})
    session = MagicMock()
    session.post.return_value = reply
    assert (
        query.post("https://example.invalid", {}, {}, session=session, timeout=(1, 2))["songs"]
        == []
    )
    assert session.post.call_args.kwargs["timeout"] == (1, 2)
    reply.__exit__.assert_called_once()


@pytest.mark.parametrize(
    "payload,expected",
    [
        ([], ResponseError),
        ({}, ResponseError),
        ({"code": -460, "message": "网络环境存在风险"}, APIError),
        ({"code": -462, "message": "需要验证"}, APIError),
        ({"code": 301}, APIError),
        ({"code": 50000005}, APIError),
    ],
)
def test_business_errors_never_turn_into_keyerror(payload, expected):
    session = MagicMock()
    session.post.return_value = response(payload)
    with pytest.raises(expected) as caught:
        query.post("https://example.invalid", {}, {}, session=session)
    if expected is APIError:
        assert caught.value.code == payload["code"]


@pytest.mark.parametrize("status", [401, 403, 405, 429, 500])
def test_http_error_keeps_status(status):
    session = MagicMock()
    session.post.return_value = response(status=status)
    with pytest.raises(RequestError) as caught:
        query.post("https://example.invalid", {}, {}, session=session)
    assert caught.value.status_code == status


def test_invalid_json_and_timeout():
    session = MagicMock()
    session.post.return_value = response()
    session.post.return_value.json.side_effect = ValueError("invalid")
    with pytest.raises(ResponseError):
        query.post("https://example.invalid", {}, {}, session=session)
    session.post.side_effect = requests.Timeout()
    with pytest.raises(RequestError):
        query.post("https://example.invalid", {}, {}, session=session)


def test_owned_http_session(monkeypatch):
    session = MagicMock()
    session.__enter__.return_value = session
    session.post.return_value = response({"code": "200"})
    monkeypatch.setattr(query.requests, "Session", lambda: session)
    assert query.post("https://example.invalid", {}, {})["code"] == "200"
    session.__exit__.assert_called_once()


@pytest.mark.parametrize(
    "timeout", [0, -1, True, None, float("nan"), float("inf"), (), (1, 2, 3), (1, 0)]
)
def test_invalid_timeout(timeout):
    with pytest.raises(ValueError):
        Api(timeout=timeout)


def test_client_cookie_csrf_config_and_close(monkeypatch):
    captured = []
    monkeypatch.setattr(
        query, "post", lambda *args, **kw: captured.append((args, kw)) or {"code": 200}
    )
    monkeypatch.setattr(encrypt, "encrypted_request", lambda data, method="": data)
    cookie = {"MUSIC_U": "test-token", "__csrf": "test-csrf"}
    with Api(cookie=cookie, timeout=3, proxies={"https": "http://localhost:8888"}) as api:
        cookie["MUSIC_U"] = "changed"
        api.send("/weapi/test", {"id": 1})
        assert api.session.cookies.get("MUSIC_U", domain="music.163.com") == "test-token"
        assert captured[0][0][0] == "https://music.163.com/weapi/test"
        assert captured[0][0][2]["csrf_token"] == "test-csrf"
        assert captured[0][1]["session"] is api.session
        assert "Cookie" not in api.headers and "cookie" not in api.headers
    with pytest.raises(RuntimeError):
        api.send("/weapi/test")
    with Api(cookie="MUSIC_U=test; __csrf=csrf") as api:
        assert api.options["cookie"]["__csrf"] == "csrf"
    with Api() as api:
        assert "MUSIC_U" not in api.options["cookie"]


@pytest.mark.parametrize("cookie", [False, 1, [], "not a cookie"])
def test_bad_cookie(cookie):
    with pytest.raises(ValueError):
        Api(cookie=cookie)


def test_random_key_generation():
    first, second = encrypt.create_key(16), encrypt.create_key(16)
    assert len(first) == len(second) == 16
    assert first != second


def test_required_endpoint_parameters(api_send):
    routes, calls = api_send
    routes["/weapi/v3/song/detail"] = {"code": 200, "songs": []}
    routes["/weapi/v1/resource/comments/R_SO_4_1"] = {"code": 200}
    routes["/weapi/song/enhance/player/url/v1"] = {"code": 200, "data": []}
    with Api() as api:
        api.get_song_detail({"ID": [1]})
        api.get_commets({"ID": 1})
        api.get_song_url({"ID": [1], "level": "standard"})
    assert json.loads(calls[0][1]["ids"]) == [1]
    assert json.loads(calls[0][1]["c"]) == [{"id": 1}]
    assert calls[1][1] == {"rid": "1", "offset": 0, "beforeTime": 0, "limit": 20}
    assert calls[2][1] == {"ids": [1], "level": "standard", "encodeType": "aac"}


def test_server_issued_cookies_reach_followup_objects(monkeypatch):
    def reply(url, headers, data, *, session, timeout):
        session.cookies.set("NMTID", "anonymous-session", domain=".music.163.com", path="/")
        session.cookies.set("foreign", "not-copied", domain="example.invalid", path="/")
        return {"code": 200}

    monkeypatch.setattr(query, "post", reply)
    with Api() as api:
        api.send("/weapi/test")
        assert api.options["cookie"]["NMTID"] == "anonymous-session"
        assert "foreign" not in api.options["cookie"]
        with Api(**api.options) as followup:
            assert (
                followup.session.cookies.get("NMTID", domain="music.163.com") == "anonymous-session"
            )
