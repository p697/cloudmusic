"""NetEase read-only endpoints and a reusable, caller-configured connection."""

import json
import math
from collections.abc import Mapping
from http.cookies import SimpleCookie

import requests

from . import encrypt, query


class Api:
    def __init__(self, *, cookie=None, timeout=(5, 20), proxies=None):
        values = timeout if isinstance(timeout, (list, tuple)) else (timeout,)
        if len(values) not in (1, 2) or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0
            for v in values
        ):
            raise ValueError("timeout 必须是正数或 (连接超时, 读取超时)")
        self.timeout = tuple(values) if len(values) == 2 else values[0]
        self.proxies = dict(proxies or {})
        cookies = {"os": "pc"}
        if isinstance(cookie, str):
            parsed = SimpleCookie()
            parsed.load(cookie)
            if cookie.strip() and not parsed:
                raise ValueError("cookie 格式无效")
            cookies.update({key: value.value for key, value in parsed.items()})
        elif cookie is not None:
            if not isinstance(cookie, Mapping):
                raise ValueError("cookie 必须是字符串或字典")
            cookies.update(cookie)
        self.options = {
            "cookie": dict(cookies),
            "timeout": self.timeout,
            "proxies": dict(self.proxies),
        }
        self.session = requests.Session()
        self.session.proxies.update(self.proxies)
        for name, value in cookies.items():
            self.session.cookies.set(name, str(value), domain="music.163.com", path="/")
        self.headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://music.163.com/"}
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.session.close()
        self._closed = True

    def send(self, url, param=None, method=""):
        if self._closed:
            raise RuntimeError("Client 已关闭")
        if url.startswith("/"):
            url = "https://music.163.com" + url
        params = dict(param or {})
        params.setdefault("csrf_token", self.options["cookie"].get("__csrf", ""))
        try:
            return query.post(
                url,
                self.headers,
                encrypt.encrypted_request(params, method),
                session=self.session,
                timeout=self.timeout,
            )
        finally:
            # Preserve server-issued session cookies for lazy requests on returned objects.
            self.options["cookie"].update(
                {
                    cookie.name: cookie.value
                    for cookie in self.session.cookies
                    if cookie.domain.lstrip(".") == "music.163.com"
                }
            )

    def get_song_url(self, para):
        return self.send(
            "/weapi/song/enhance/player/url/v1",
            {
                "ids": para["ID"],
                "level": para["level"],
                "encodeType": "aac",
            },
        )

    def search(self, para):
        return self.send(
            "/weapi/search/get",
            {
                "s": para["string"],
                "type": 1,
                "offset": para.get("offset", 0),
                "limit": para["number"],
            },
        )

    def get_commets(self, para):
        # Retain the historical internal spelling for integrations using Api.
        return self.send(
            "/weapi/v1/resource/comments/R_SO_4_{}".format(para["ID"]),
            {
                "rid": str(para["ID"]),
                "offset": para.get("offset", 0),
                "beforeTime": 0,
                "limit": para.get("limit", 20),
            },
        )

    def get_comment_page(self, para):
        return self.send(
            "/weapi/v2/resource/comments",
            {
                "threadId": "R_SO_4_{}".format(para["ID"]),
                "pageNo": para["page"],
                "pageSize": para["limit"],
                "sortType": 3,
                "cursor": para["cursor"],
                "showInner": True,
            },
        )

    def get_lyrics(self, para):
        return self.send("/weapi/song/lyric", {"id": para["ID"], "lv": -1, "tv": -1})

    def get_song_detail(self, para):
        return self.send(
            "/weapi/v3/song/detail",
            {
                "c": json.dumps([{"id": value} for value in para["ID"]]),
                "ids": json.dumps(para["ID"]),
            },
        )

    def get_playlist(self, para, method=""):
        return self.send("/weapi/v6/playlist/detail", {"id": para["ID"], "n": 100000, "s": 8})

    def get_album(self, para):
        return self.send("/weapi/v1/album/{}".format(para["ID"]))

    def get_userInfo(self, para):
        return self.send("/weapi/v1/user/detail/{}".format(para["ID"]))

    def get_userPlayerlist(self, para):
        return self.send(
            "/weapi/user/playlist",
            {
                "uid": para["ID"],
                "offset": para.get("offset", 0),
                "limit": para.get("limit", 100),
            },
        )

    def get_userRecord(self, para):
        return self.send("/weapi/v1/play/record", {"uid": para["ID"], "type": para.get("type", 0)})
