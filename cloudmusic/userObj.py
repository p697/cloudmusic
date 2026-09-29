"""User metadata and read-only playlist/listening-history access."""

from .api import Api
from .exceptions import IncompleteResultError
from .musicObj import createObj
from .validation import field, integer


def createUser(ID, **options):
    with Api(**options) as api:
        return User(api.get_userInfo({"ID": integer(ID, "id", 1)}), options=api.options)


class User:
    def __init__(self, info, *, options=None):
        self._options = options or {}
        profile = field(info, "profile", dict)
        self.id = str(field(profile, "userId", int))
        self.nickname = profile.get("nickname") or ""
        self.nickName = self.nickname
        self.sex = profile.get("gender", 0)
        self.level = info.get("level", 0)
        self.listenSongs = info.get("listenSongs", 0)
        for key in (
            "createTime",
            "avatarUrl",
            "city",
            "province",
            "vipType",
            "birthday",
            "signature",
            "follows",
            "eventCount",
            "playlistCount",
        ):
            setattr(self, key, profile.get(key))
        self.fans = profile.get("followeds", 0)

    def getPlaylist(self):
        result, seen, offset = [], set(), 0
        with Api(**self._options) as api:
            while True:
                data = api.get_userPlayerlist({"ID": self.id, "offset": offset, "limit": 100})
                page = field(data, "playlist", list)
                added = 0
                for playlist in page:
                    playlist_id = field(playlist, "id", int)
                    if playlist_id in seen:
                        continue
                    seen.add(playlist_id)
                    result.append(
                        {
                            "id": playlist_id,
                            "creatorId": playlist.get("userId"),
                            **{
                                key: playlist.get(key)
                                for key in (
                                    "playCount",
                                    "createTime",
                                    "coverImgUrl",
                                    "name",
                                    "updateTime",
                                    "tags",
                                )
                            },
                        }
                    )
                    added += 1
                if not data.get("more", False):
                    return result
                if not added:
                    raise IncompleteResultError("用户歌单分页未继续前进", result)
                offset += len(page)

    def getRecord(self, recordType=0):
        record_type = 1 if integer(recordType, "recordType") else 0
        with Api(**self._options) as api:
            data = api.get_userRecord({"ID": self.id, "type": record_type})
            rows = field(data, "weekData" if record_type else "allData", list)
            details = [field(row, "song", dict) for row in rows]
            songs = createObj(
                [field(song, "id", int) for song in details],
                api=api,
                options=api.options,
                details=details,
            )
        by_id = {song.id: song for song in songs}
        return [
            {"score": field(row, "score", int), "music": by_id[str(row["song"]["id"])]}
            for row in rows
        ]
