import copy

import pytest
import requests

from cloudmusic.api import Api


def pytest_addoption(parser):
    parser.addoption("--live", action="store_true", help="Run opt-in NetEase network checks")
    parser.addoption(
        "--cookie-env",
        default=None,
        help="Explicit environment variable containing a cookie for live tests",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--live"):
        for item in items:
            if "live" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="Pass --live to enable real network checks")
                )


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch, request):
    if "live" in request.keywords:
        return
    original = requests.Session.request

    def guarded(self, method, url, *args, **kwargs):
        if url.startswith("http://127.0.0.1:"):
            return original(self, method, url, *args, **kwargs)
        pytest.fail("Unexpected external request: {} {}".format(method, url))

    monkeypatch.setattr(requests.Session, "request", guarded)


def song(song_id):
    return {
        "id": song_id,
        "name": "歌曲{}".format(song_id),
        "alia": [],
        "ar": [{"id": 10, "name": "歌手"}],
        "al": {"id": 20, "name": "专辑", "picUrl": "https://example.invalid/cover"},
    }


def audio(song_id, **overrides):
    return {
        "id": song_id,
        "url": "https://example.invalid/audio",
        "level": "higher",
        "size": 4,
        "type": "mp3",
        "code": 200,
        **overrides,
    }


@pytest.fixture
def api_send(monkeypatch):
    routes, calls = {}, []

    def send(self, url, param=None, method=""):
        params = copy.deepcopy(param or {})
        calls.append((url, params))
        value = routes[url]
        if callable(value):
            return value(params)
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value)

    monkeypatch.setattr(Api, "send", send)
    return routes, calls
