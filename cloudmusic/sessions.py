"""Reusable public client; returned objects retain configuration, not open sockets."""

from .api import Api
from .exceptions import IncompleteResultError, ResponseError
from .musicObj import createObj, validate_level
from .validation import field, ids, integer


class Session:
    def __init__(self, *, cookie=None, timeout=(5, 20), proxies=None, level="higher"):
        self.level = validate_level(level)
        self.api = Api(cookie=cookie, timeout=timeout, proxies=proxies)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.api.close()

    def _music(self, song_ids, details=None):
        return createObj(
            song_ids, self.level, api=self.api, options=self.api.options, details=details
        )

    def getMusic(self, para):
        songs = self._music(ids(para))
        return songs if isinstance(para, (list, tuple)) else songs[0]

    def getPlaylist(self, para):
        playlist_id = integer(para, "id", 1)
        data = field(self.api.get_playlist({"ID": playlist_id}), "playlist", dict)
        tracks = field(data, "tracks", list)
        track_ids = field(data, "trackIds", list)
        song_ids = [field(track, "id", int) for track in track_ids]
        result = self._music(song_ids, details=tracks)
        expected = field(data, "trackCount", int)
        if len(song_ids) != expected:
            raise IncompleteResultError(
                "网易云只返回了歌单的部分歌曲；可能需要登录或访问权限",
                result,
                expected,
            )
        return result

    def getAlbum(self, para):
        album_id = integer(para, "id", 1)
        songs = field(self.api.get_album({"ID": album_id}), "songs", list)
        return self._music([field(song, "id", int) for song in songs], details=songs)

    def getUser(self, para):
        from .userObj import User

        user_id = integer(para, "id", 1)
        return User(self.api.get_userInfo({"ID": user_id}), options=self.api.options)

    def request(self, clas, para):
        methods = {
            "song": self.getMusic,
            "playlist": self.getPlaylist,
            "album": self.getAlbum,
            "user": self.getUser,
        }
        if clas not in methods:
            raise ValueError("未知请求类型：{}".format(clas))
        return methods[clas](para)

    def search(self, content, number=5):
        if not isinstance(content, str) or not content.strip():
            raise ValueError("搜索关键词不能为空")
        number = integer(number, "number")
        song_ids, seen, offset = [], set(), 0
        while len(song_ids) < number:
            limit = min(100, number)
            result = field(
                self.api.search({"string": content, "number": limit, "offset": offset}),
                "result",
                dict,
            )
            if "songs" not in result and result.get("songCount") != 0:
                raise ResponseError("搜索响应缺少歌曲列表或零结果计数")
            page = result.get("songs", [])
            if not isinstance(page, list):
                raise ResponseError("搜索结果中的 songs 格式无效")
            added = 0
            for song in page:
                song_id = field(song, "id", int)
                if song_id not in seen:
                    song_ids.append(song_id)
                    seen.add(song_id)
                    added += 1
            offset += len(page)
            more = (
                field(result, "hasMore", bool)
                if "hasMore" in result
                else (offset < field(result, "songCount", int))
            )
            if not more:
                break
            if added == 0:
                raise IncompleteResultError(
                    "搜索分页没有继续返回新歌曲", self._music(song_ids), number
                )
        return self._music(song_ids[:number])

    def comment(self, para):
        song_id = str(integer(para["ID"], "id", 1))
        clas = para["clas"]
        if clas == "count":
            return field(self.api.get_commets({"ID": song_id, "limit": 20}), "total", int)
        number = integer(para["number"], "number")
        if not number:
            return []
        if clas == "hot":
            data = self.api.get_commets({"ID": song_id, "limit": 20})
            return self.datalizeComment(field(data, "hotComments", list), min(number, 15))
        if clas != "new":
            raise ValueError("未知评论类型")
        comments, seen, cursors = [], set(), {"0"}
        cursor, page_number = "0", 1
        while len(comments) < number:
            data = field(
                self.api.get_comment_page(
                    {
                        "ID": song_id,
                        "page": page_number,
                        "limit": min(20, number),
                        "cursor": cursor,
                    }
                ),
                "data",
                dict,
            )
            page = field(data, "comments", list)
            previous_count = len(comments)
            for comment in page:
                comment_id = field(comment, "commentId", int)
                if comment_id not in seen:
                    seen.add(comment_id)
                    comments.append(comment)
            if len(comments) >= number or not field(data, "hasMore", bool):
                break
            next_cursor = str(data.get("cursor") or "")
            if not next_cursor or next_cursor in cursors or len(comments) == previous_count:
                raise IncompleteResultError(
                    "评论分页未继续前进，已停止以避免重复请求",
                    self.datalizeComment(comments, number),
                    number,
                )
            cursors.add(next_cursor)
            cursor, page_number = next_cursor, page_number + 1
        return self.datalizeComment(comments, number)

    def datalizeComment(self, comments, number):
        output = []
        for comment in comments[:number]:
            user = comment.get("user") or {}
            output.append(
                {
                    "commentId": comment.get("commentId"),
                    "likeCount": comment.get("likedCount", 0),
                    "content": comment.get("content") or "",
                    "time": comment.get("time"),
                    "nickName": user.get("nickname") or "",
                    "userId": str(user.get("userId", "")),
                    "avatarUrl": user.get("avatarUrl") or "",
                    "vipType": user.get("vipType", 0),
                    "userType": user.get("userType", 0),
                }
            )
        return output

    def downloader(self, procs=2, dirs=""):
        from .download import Downloader

        return Downloader(procs, dirs)
