import json
from concurrent.futures import ThreadPoolExecutor

import pytest

import cloudmusic
from cloudmusic import APIError, NotFoundError, ResponseError, UnavailableError
from cloudmusic.api import Api
from cloudmusic.musicObj import _PlaybackBatch, createObj
from conftest import audio, song

DETAIL = "/weapi/v3/song/detail"
URL = "/weapi/song/enhance/player/url/v1"


def default_details(params):
    return {"code": 200, "songs": [song(item["id"]) for item in reversed(json.loads(params["c"]))]}


def test_input_shape_order_duplicates_and_empty(api_send):
    routes, calls = api_send
    routes[DETAIL] = default_details
    assert cloudmusic.getMusic(1).id == "1"
    assert [m.id for m in cloudmusic.getMusic([2, 1, 2])] == ["2", "1", "2"]
    assert isinstance(cloudmusic.getMusic([1]), list)
    assert isinstance(cloudmusic.getMusic((1,)), list)
    calls.clear()
    assert cloudmusic.getMusic([]) == []
    assert calls == []


@pytest.mark.parametrize("bad", [None, True, 0, -1, 1.5, "abc", [1, False], [0], {}])
def test_invalid_ids_never_make_request(bad, api_send):
    with pytest.raises(ValueError):
        cloudmusic.getMusic(bad)
    assert api_send[1] == []


def test_missing_metadata_cannot_reuse_another_song(api_send):
    api_send[0][DETAIL] = {"code": 200, "songs": [song(1)]}
    with pytest.raises(NotFoundError) as caught:
        cloudmusic.getMusic([1, 2])
    assert caught.value.ids == [2]


def test_unexpected_metadata_schema(api_send):
    api_send[0][DETAIL] = {"code": 200, "songs": [{"id": 1}]}
    with pytest.raises(ResponseError):
        cloudmusic.getMusic(1)


def test_metadata_does_not_require_audio_and_lazy_batch_reuses_request(api_send):
    routes, calls = api_send
    routes[DETAIL] = default_details
    routes[URL] = {"code": 200, "data": [audio(2, level="standard"), audio(1)]}
    music = cloudmusic.getMusic([1, 2])
    assert [m.name for m in music] == ["歌曲1", "歌曲2"]
    assert len(calls) == 1
    assert music[1].url == "https://example.invalid/audio"
    assert music[1].level == "standard"
    assert music[0].size == 4 and music[0].type == "mp3"
    assert music[0].freeTrialInfo is None
    assert len(calls) == 2
    assert calls[1][1]["ids"] == [1, 2]
    assert repr(music[0]) == "<Music object - 1>"


def test_batching_for_large_queries(api_send):
    routes, calls = api_send
    routes[DETAIL] = default_details
    result = cloudmusic.getMusic(list(range(1, 452)))
    assert len(result) == 451
    assert [len(json.loads(params["c"])) for _, params in calls] == [200, 200, 51]


def test_concurrent_audio_lookup_uses_one_batch(api_send):
    routes, calls = api_send
    routes[DETAIL] = default_details
    routes[URL] = {"code": 200, "data": [audio(i) for i in range(1, 11)]}
    songs = cloudmusic.getMusic(list(range(1, 11)))
    with ThreadPoolExecutor(10) as pool:
        assert all(pool.map(lambda m: m.url, songs))
    assert len(calls) == 2


def test_expired_audio_is_refreshed(api_send, monkeypatch):
    routes, calls = api_send
    routes[URL] = {"code": 200, "data": [audio(1)]}
    batch = _PlaybackBatch([1], "higher", {})
    monkeypatch.setattr("cloudmusic.musicObj.time.monotonic", lambda: 10)
    assert batch.get(1)["url"]
    monkeypatch.setattr("cloudmusic.musicObj.time.monotonic", lambda: 71)
    assert batch.get(1)["url"]
    assert len(calls) == 2


def test_audio_challenge_preserves_metadata_and_is_not_repeated(api_send, monkeypatch):
    routes, calls = api_send
    monkeypatch.setattr("cloudmusic.musicObj.time.monotonic", lambda: 10)
    routes[DETAIL] = default_details
    routes[URL] = APIError(-460, "network risk")
    music = cloudmusic.getMusic(1)
    with pytest.raises(APIError):
        _ = music.url
    assert music.name == "歌曲1"
    routes[URL] = {"code": 200, "data": [audio(1)]}
    with pytest.raises(APIError):
        _ = music.url
    assert len(calls) == 2
    monkeypatch.setattr("cloudmusic.musicObj.time.monotonic", lambda: 71)
    assert music.url


def test_audio_missing_null_or_trial_is_explicit(api_send):
    routes, _ = api_send
    routes[DETAIL] = default_details
    for data in ([], [audio(1, url=None)], [audio(1, freeTrialInfo={"start": 0, "end": 30})]):
        routes[URL] = {"code": 200, "data": data}
        music = cloudmusic.getMusic(1)
        with pytest.raises(UnavailableError):
            music.download()


def test_quality_change_keeps_directory_and_metadata(api_send, monkeypatch, tmp_path):
    routes, calls = api_send
    routes[DETAIL] = default_details
    routes[URL] = {"code": 200, "data": [audio(1, type="flac", level="lossless")]}
    captured = []
    monkeypatch.setattr(
        "cloudmusic.download.download",
        lambda dirs, music, **kwargs: captured.append((dirs, music, kwargs)) or "saved",
    )
    music = cloudmusic.getMusic(1)
    assert music.download(tmp_path, "lossless") == "saved"
    assert captured[0][0] == tmp_path and captured[0][1] is music
    assert captured[0][2]["audio"]["type"] == "flac"
    assert calls[-1][1]["level"] == "lossless"
    with pytest.raises(ValueError):
        music.download(level="magic")


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"code": 200}, ["", ""]),
        ({"code": 200, "lrc": {"lyric": "原文"}}, ["原文", ""]),
        ({"code": 200, "lrc": None, "tlyric": None}, ["", ""]),
        ({"code": 200, "lrc": {"lyric": "原文"}, "tlyric": {"lyric": "译文"}}, ["原文", "译文"]),
    ],
)
def test_lyrics_without_audio_or_translation(api_send, payload, expected):
    routes, calls = api_send
    routes[DETAIL] = default_details
    routes["/weapi/song/lyric"] = payload
    assert cloudmusic.getMusic(1).getLyrics() == expected
    assert len(calls) == 2


def test_objects_retain_configuration_after_client_close(api_send):
    routes, _ = api_send
    routes[DETAIL] = default_details
    with cloudmusic.Client(cookie="MUSIC_U=test", timeout=2) as client:
        music = client.getMusic(1)
    assert music._options["cookie"]["MUSIC_U"] == "test"
    assert music._options["timeout"] == 2
    routes[URL] = {"code": 200, "data": [audio(1)]}
    assert music.url


def test_helpers_and_alias_metadata(api_send, capsys):
    detail = song(1)
    detail["alia"] = ["别名"]
    api_send[0][DETAIL] = {"code": 200, "songs": [detail]}
    assert createObj([1])[0].name == "歌曲1 别名"
    with Api() as api:
        assert createObj([], api=api) == []
    cloudmusic.help()
    assert "getMusic" in capsys.readouterr().out


def test_invalid_lyrics_shape_is_response_error(api_send):
    routes, _ = api_send
    routes[DETAIL] = default_details
    routes["/weapi/song/lyric"] = {"code": 200, "lrc": "not an object"}
    with pytest.raises(ResponseError):
        cloudmusic.getMusic(1).getLyrics()
    with pytest.raises(ValueError):
        cloudmusic.getMusic(1).download(level="")
