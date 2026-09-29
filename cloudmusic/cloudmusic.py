"""Convenience functions; use Client for explicit configuration and connection reuse."""

from .sessions import Session as Client


def getMusic(para):
    with Client() as client:
        return client.getMusic(para)


def getPlaylist(para):
    with Client() as client:
        return client.getPlaylist(para)


def getAlbum(para):
    with Client() as client:
        return client.getAlbum(para)


def search(para, number=5):
    with Client() as client:
        return client.search(para, number)


def createLoader(procs=2, dirs=""):
    from .download import Downloader

    return Downloader(procs, dirs)


def getUser(para):
    with Client() as client:
        return client.getUser(para)


def help():
    print(
        "cloudmusic: getMusic(id 或 id 列表), getPlaylist(id), getAlbum(id), "
        "search(关键词, number=5), getUser(id), createLoader(procs=2, dirs='')。\n"
        "使用 Client(cookie=..., timeout=(5, 20), proxies=...) 配置会话。\n"
        "文档：https://github.com/p697/cloudmusic#readme"
    )
