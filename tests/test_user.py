import pytest

import cloudmusic
from cloudmusic import IncompleteResultError, ResponseError
from cloudmusic.userObj import createUser
from conftest import song


def user():
    return cloudmusic.User({"profile": {"userId": 1, "nickname": "用户"}})


def test_user_optional_fields_and_public_alias(api_send):
    api_send[0]["/weapi/v1/user/detail/1"] = {
        "code": 200,
        "profile": {"userId": 1, "nickname": "用户"},
    }
    value = cloudmusic.getUser(1)
    assert value.id == "1"
    assert value.nickname == value.nickName == "用户"
    assert value.level == value.listenSongs == value.fans == 0
    assert createUser(1).id == "1"
    with pytest.raises(ResponseError):
        cloudmusic.User({"profile": None})


def test_user_playlist_paginates_without_duplicates(api_send):
    routes, calls = api_send
    pages = iter(
        [
            {"playlist": [{"id": 10, "name": "a"}], "more": True},
            {"playlist": [{"id": 10}, {"id": 11, "name": "b"}], "more": False},
        ]
    )
    routes["/weapi/user/playlist"] = lambda _: next(pages)
    assert [p["id"] for p in user().getPlaylist()] == [10, 11]
    assert [p["offset"] for _, p in calls] == [0, 1]


def test_user_playlist_stalled_page(api_send):
    api_send[0]["/weapi/user/playlist"] = {"playlist": [], "more": True}
    with pytest.raises(IncompleteResultError):
        user().getPlaylist()


@pytest.mark.parametrize("record_type,key", [(0, "allData"), (1, "weekData"), (2, "weekData")])
def test_record_only_fetches_requested_period_and_preserves_scores(api_send, record_type, key):
    routes, calls = api_send
    routes["/weapi/v1/play/record"] = {
        "code": 200,
        key: [
            {"song": song(2), "score": 100},
            {"song": song(1), "score": 20},
        ],
    }
    result = user().getRecord(record_type)
    assert [(r["music"].id, r["score"]) for r in result] == [("2", 100), ("1", 20)]
    assert len(calls) == 1
    assert calls[0][1]["type"] == (1 if record_type else 0)
    routes["/weapi/v1/play/record"] = {"code": 200, key: []}
    assert user().getRecord(record_type) == []
