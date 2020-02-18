from . import sessions


def getMusic(para):
    with sessions.Session() as session:
        return session.request("song", para)


def getPlaylist(para):
    with sessions.Session() as session:
        return session.request("playlist", para)


def getAlbum(para):
    with sessions.Session() as session:
        return session.request("album", para)


def search(para, number=5):
    with sessions.Session() as session:
        return session.search(para, number)


def createLoader(procs=2, dirs=""):
    with sessions.Session() as session:
        return session.downloader(procs, dirs)


def getUser(para):
    with sessions.Session() as session:
        return session.request("user", para)


def help():
    print("这是帮助")

