import pytest

import cloudmusic
from cloudmusic import IncompleteResultError, ResponseError
from cloudmusic.sessions import Session
from conftest import song

PLAYLIST = "/weapi/v6/playlist/detail"
SEARCH = "/weapi/search/get"
COMMENT = "/weapi/v2/resource/comments"


def comment(comment_id):
    return {
        "commentId": comment_id,
        "content": str(comment_id),
        "time": comment_id,
        "likedCount": 3,
        "user": {"userId": 10, "nickname": "用户"},
    }


@pytest.mark.parametrize("track_ids", [[], [1], [3, 1, 2]])
def test_playlist_complete_empty_single_and_order(api_send, track_ids):
    routes, calls = api_send
    routes[PLAYLIST] = {
        "code": 200,
        "playlist": {
            "trackCount": len(track_ids),
            "trackIds": [{"id": i} for i in track_ids],
            "tracks": [song(i) for i in reversed(track_ids)],
        },
    }
    assert [m.id for m in cloudmusic.getPlaylist(1)] == list(map(str, track_ids))
    assert len(calls) == 1  # Existing details reused, no audio or duplicate metadata request.


def test_playlist_hydrates_track_ids_and_detects_truncation(api_send):
    routes, calls = api_send
    routes[PLAYLIST] = {
        "code": 200,
        "playlist": {
            "trackCount": 3,
            "trackIds": [{"id": 1}, {"id": 2}],
            "tracks": [song(1)],
        },
    }
    routes["/weapi/v3/song/detail"] = {"code": 200, "songs": [song(2)]}
    with pytest.raises(IncompleteResultError) as caught:
        cloudmusic.getPlaylist(1)
    assert caught.value.expected_count == 3
    assert caught.value.actual_count == 2
    assert [m.id for m in caught.value.partial_result] == ["1", "2"]
    assert len(calls) == 2


@pytest.mark.parametrize("song_ids", [[], [1], [3, 2, 1]])
def test_album_preserves_order_without_extra_fetch(api_send, song_ids):
    routes, calls = api_send
    routes["/weapi/v1/album/20"] = {"code": 200, "songs": [song(i) for i in song_ids]}
    assert [m.id for m in cloudmusic.getAlbum(20)] == list(map(str, song_ids))
    assert len(calls) == 1


def test_search_pages_and_deduplicates(api_send):
    routes, calls = api_send
    pages = iter(
        [
            {"songs": [{"id": 1}, {"id": 2}], "hasMore": True},
            {"songs": [{"id": 2}, {"id": 3}], "hasMore": True},
            {"songs": [{"id": 4}], "hasMore": False},
        ]
    )
    routes[SEARCH] = lambda _: {"code": 200, "result": next(pages)}
    routes["/weapi/v3/song/detail"] = {"code": 200, "songs": [song(i) for i in range(1, 5)]}
    assert [m.id for m in cloudmusic.search('白日 "test"', 4)] == ["1", "2", "3", "4"]
    search_calls = [p for path, p in calls if path == SEARCH]
    assert [p["offset"] for p in search_calls] == [0, 2, 4]
    assert search_calls[0]["s"] == '白日 "test"'


def test_search_empty_and_no_progress(api_send):
    routes, calls = api_send
    assert cloudmusic.search("anything", 0) == []
    assert calls == []
    routes[SEARCH] = {"code": 200, "result": {"songCount": 0}}
    assert cloudmusic.search("no matches") == []
    routes[SEARCH] = {"code": 200, "result": {"songs": [], "hasMore": True}}
    with pytest.raises(IncompleteResultError):
        cloudmusic.search("broken")
    routes[SEARCH] = {"code": 200, "result": {"songs": "invalid"}}
    with pytest.raises(ResponseError):
        cloudmusic.search("broken")


@pytest.mark.parametrize("keyword,number", [("", 1), ("  ", 1), (None, 1), ("a", -1), ("a", 1.2)])
def test_bad_search_input(keyword, number):
    with pytest.raises(ValueError):
        cloudmusic.search(keyword, number)


def test_comments_100_unique_with_short_pages_and_overlap(api_send):
    routes, calls = api_send

    def page(params):
        cursor = int(params["cursor"])
        start = max(1, cursor)  # One overlapping item between pages.
        end = min(101, start + params["pageSize"])
        if cursor == 0:
            end = 19  # Service can return fewer items while hasMore remains true.
        rows = [comment(i) for i in range(start, end)]
        return {
            "code": 200,
            "data": {"comments": rows, "hasMore": end < 101, "cursor": str(end - 1)},
        }

    routes[COMMENT] = page
    with Session() as client:
        result = client.comment({"ID": 1, "clas": "new", "number": 100})
    assert [c["commentId"] for c in result] == list(range(1, 101))
    assert all(0 < params["pageSize"] <= 20 for _, params in calls)
    assert all(params["sortType"] == 3 for _, params in calls)


def test_comments_end_before_requested_count(api_send):
    api_send[0][COMMENT] = {
        "code": 200,
        "data": {"comments": [comment(1)], "hasMore": False, "cursor": "1"},
    }
    with Session() as client:
        assert len(client.comment({"ID": 1, "clas": "new", "number": 100})) == 1


@pytest.mark.parametrize("cursor,rows", [("0", [comment(1)]), (None, []), ("", [comment(1)])])
def test_comment_pagination_stops_when_stalled(api_send, cursor, rows):
    api_send[0][COMMENT] = {
        "code": 200,
        "data": {"comments": rows, "hasMore": True, "cursor": cursor},
    }
    with Session() as client, pytest.raises(IncompleteResultError):
        client.comment({"ID": 1, "clas": "new", "number": 100})
    assert len(api_send[1]) == 1


def test_comment_wrappers_count_hot_deleted_user_and_zero(api_send):
    routes, calls = api_send
    routes["/weapi/v3/song/detail"] = {"code": 200, "songs": [song(1)]}
    routes["/weapi/v1/resource/comments/R_SO_4_1"] = {
        "code": 200,
        "total": 123,
        "hotComments": [{**comment(1), "user": None}],
    }
    routes[COMMENT] = {"code": 200, "data": {"comments": [], "hasMore": False}}
    music = cloudmusic.getMusic(1)
    assert music.getCommentsCount() == 123
    assert music.getHotComments()[0]["nickName"] == ""
    assert music.getComments(1) == []
    calls.clear()
    assert music.getHotComments(0) == []
    assert music.getComments(0) == []
    assert calls == []
    with pytest.raises(ValueError):
        music.getComments(-1)


def test_dispatch_and_invalid_operations(api_send):
    routes, _ = api_send
    routes["/weapi/v3/song/detail"] = {"code": 200, "songs": [song(1)]}
    with Session() as client:
        assert client.request("song", 1).id == "1"
        assert client.downloader().procs == 2
        with pytest.raises(ValueError):
            client.request("unknown", 1)
        with pytest.raises(ValueError):
            client.comment({"ID": 1, "clas": "unknown", "number": 1})
    with pytest.raises(ValueError):
        Session(level="magic")


def test_search_rejects_missing_payload_and_uses_total_without_more_flag(api_send):
    routes, _ = api_send
    routes[SEARCH] = {"code": 200, "result": {}}
    with pytest.raises(ResponseError):
        cloudmusic.search("test")
    pages = iter(
        [
            {"songs": [{"id": 1}], "songCount": 2},
            {"songs": [{"id": 2}], "songCount": 2},
        ]
    )
    routes[SEARCH] = lambda _: {"code": 200, "result": next(pages)}
    routes["/weapi/v3/song/detail"] = {"code": 200, "songs": [song(1), song(2)]}
    assert [m.id for m in cloudmusic.search("test", 2)] == ["1", "2"]


def test_duplicate_comment_page_with_new_cursor_does_not_loop(api_send):
    routes, calls = api_send
    routes[COMMENT] = lambda params: {
        "code": 200,
        "data": {"comments": [comment(1)], "hasMore": True, "cursor": str(params["pageNo"])},
    }
    with Session() as client, pytest.raises(IncompleteResultError) as caught:
        client.comment({"ID": 1, "clas": "new", "number": 10})
    assert len(calls) == 2
    assert len(caught.value.partial_result) == 1
