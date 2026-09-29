"""Opt-in, low-volume checks. Remote restrictions are failures, never silent passes."""

import os

import pytest

import cloudmusic

pytestmark = pytest.mark.live
SONG_ID = 1347630432
PLAYLIST_ID = 310729011


@pytest.fixture(scope="module")
def live_client(request):
    cookie_env = request.config.getoption("--cookie-env")
    if cookie_env and not os.environ.get(cookie_env):
        raise pytest.UsageError("Missing cookie environment variable: {}".format(cookie_env))
    with cloudmusic.Client(cookie=os.environ[cookie_env] if cookie_env else None) as client:
        yield client


@pytest.fixture(scope="module")
def sample(live_client):
    return live_client.getMusic(SONG_ID)


def test_live_song_metadata(sample):
    assert sample.id == str(SONG_ID)
    assert sample.name and sample.artist and sample.albumId


def test_live_search(live_client):
    results = live_client.search("白日", 5)
    assert len(results) == 5
    assert len({song.id for song in results}) == 5
    assert all(song.name for song in results)


def test_live_playlist_complete(live_client):
    # Client checks trackCount against the returned IDs before returning success.
    songs = live_client.getPlaylist(PLAYLIST_ID)
    assert len(songs) > 1
    assert len({song.id for song in songs}) == len(songs)
    assert all(song.name for song in songs)


def test_live_album(sample, live_client):
    songs = live_client.getAlbum(sample.albumId)
    assert sample.id in {song.id for song in songs}


def test_live_lyrics(sample):
    original, translation = sample.getLyrics()
    assert original and isinstance(translation, str)


def test_live_comments(sample):
    assert sample.getCommentsCount() >= 100
    hot = sample.getHotComments(3)
    assert len(hot) == 3 and all(row["content"] for row in hot)
    comments = sample.getComments(100)
    assert len(comments) == 100
    assert len({row["commentId"] for row in comments}) == 100
    assert [row["time"] for row in comments] == sorted(
        (row["time"] for row in comments), reverse=True
    )
