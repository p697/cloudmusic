"""Song metadata with lazy, batched audio lookup."""

import threading
import time

from .api import Api
from .exceptions import APIError, NotFoundError, UnavailableError
from .validation import field

LEVELS = ("standard", "higher", "exhigh", "lossless")
BATCH_SIZE = 200


def validate_level(level):
    if level not in LEVELS:
        raise ValueError("level 必须是 {}".format(", ".join(LEVELS)))
    return level


class _PlaybackBatch:
    def __init__(self, ids, level, options, data=None):
        self.ids = ids
        self.level = level
        self.options = options
        self._data = data
        self._loaded_at = time.monotonic() if data is not None else 0
        self._blocked = None
        self._blocked_at = 0
        self._lock = threading.Lock()

    def get(self, song_id):
        with self._lock:
            if self._blocked and time.monotonic() - self._blocked_at < 60:
                raise APIError(*self._blocked)
            # Avoid retaining expired CDN URLs in long-running scripts.
            if self._data is None or time.monotonic() - self._loaded_at >= 60:
                try:
                    with Api(**self.options) as api:
                        rows = field(
                            api.get_song_url({"ID": self.ids, "level": self.level}), "data", list
                        )
                except APIError as exc:
                    if exc.code in (-460, -462, 301, 401, 403, 429):
                        self._blocked = (exc.code, exc.message)
                        self._blocked_at = time.monotonic()
                    raise
                self._data = {str(field(row, "id", int)): row for row in rows}
                self._loaded_at = time.monotonic()
                self._blocked = None
            return self._data.get(str(song_id), {})


def createObj(ids, level="higher", *, api=None, options=None, details=None):
    """Always return a list, in input order, including repeated IDs."""
    validate_level(level)
    if not ids:
        return []
    if api is None:
        with Api(**(options or {})) as owned:
            return createObj(ids, level, api=owned, options=owned.options, details=details)
    options = options or api.options
    known = {field(song, "id", int): song for song in (details or [])}
    unique = list(dict.fromkeys(ids))
    missing = [song_id for song_id in unique if song_id not in known]
    for offset in range(0, len(missing), BATCH_SIZE):
        rows = field(
            api.get_song_detail({"ID": missing[offset : offset + BATCH_SIZE]}), "songs", list
        )
        known.update({field(song, "id", int): song for song in rows})
    absent = [song_id for song_id in unique if song_id not in known]
    if absent:
        raise NotFoundError(absent)
    songs = {}
    for offset in range(0, len(unique), BATCH_SIZE):
        batch = unique[offset : offset + BATCH_SIZE]
        playback = _PlaybackBatch(batch, level, options)
        for song_id in batch:
            detail = known[song_id]
            album = field(detail, "al", dict)
            artists = field(detail, "ar", list)
            name = field(detail, "name", str)
            aliases = detail.get("alia") or []
            info = {
                "name": name + (" " + str(aliases[0]) if aliases else ""),
                "artist": [ar.get("name") or "" for ar in artists],
                "artistId": [ar.get("id") for ar in artists],
                "album": album.get("name") or "",
                "albumId": album.get("id"),
                "picUrl": album.get("picUrl") or "",
            }
            songs[song_id] = Music(
                song_id, level=level, info=info, options=options, playback=playback
            )
    return [songs[song_id] for song_id in ids]


class Music:
    def __init__(
        self,
        id_,
        url=None,
        level="higher",
        size=0,
        type_=None,
        info=None,
        *,
        options=None,
        playback=None,
    ):
        self.id = str(id_)
        self._options = options or {}
        self._requested_level = level
        self._playback = playback or _PlaybackBatch(
            [int(id_)],
            level,
            self._options,
            {self.id: {"url": url, "level": level, "size": size, "type": type_}},
        )
        info = info or {}
        for key, default in (
            ("name", ""),
            ("artist", []),
            ("artistId", []),
            ("album", ""),
            ("albumId", None),
            ("picUrl", ""),
        ):
            setattr(self, key, info.get(key, default))

    def __repr__(self):
        return "<Music object - {}>".format(self.id)

    @property
    def url(self):
        return self._playback.get(self.id).get("url")

    @property
    def size(self):
        return int(self._playback.get(self.id).get("size") or 0)

    @property
    def type(self):
        return self._playback.get(self.id).get("type")

    @property
    def level(self):
        """Actual audio quality returned by NetEase, which may be lower than requested."""
        return self._playback.get(self.id).get("level")

    @property
    def freeTrialInfo(self):
        return self._playback.get(self.id).get("freeTrialInfo")

    def download(self, dirs="", level=None):
        from .download import download

        selected = validate_level(self._requested_level if level is None else level)
        playback = (
            self._playback
            if selected == self._requested_level
            else _PlaybackBatch([int(self.id)], selected, self._options)
        )
        audio = playback.get(self.id)
        if not audio.get("url") or not audio.get("type"):
            raise UnavailableError("当前账号或地区无法获取这首歌的音频：{}".format(self.id))
        if audio.get("freeTrialInfo"):
            raise UnavailableError("接口仅返回试听音频，未下载为完整歌曲：{}".format(self.id))
        return download(dirs, self, audio=audio)

    def _comment(self, clas, number=15):
        from .sessions import Session

        with Session(**self._options) as session:
            return session.comment({"ID": self.id, "clas": clas, "number": number})

    def getCommentsCount(self):
        return self._comment("count")

    def getHotComments(self, number=15):
        return self._comment("hot", number)

    def getComments(self, number):
        return self._comment("new", number)

    def getLyrics(self):
        with Api(**self._options) as api:
            data = api.get_lyrics({"ID": self.id})
        output = []
        for key in ("lrc", "tlyric"):
            if data.get(key) is None:
                output.append("")
            else:
                lyrics = field(data, key, dict)
                output.append(
                    field(lyrics, "lyric", str) if lyrics.get("lyric") is not None else ""
                )
        return output
