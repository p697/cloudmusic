from . import download
from . import sessions
from . import api

import re



def createObj(ids, level):
    api = sessions.api.Api()
    musicUrl = api.get_song_url(dict(ID = ids, level = level))['data']
    musicInfo = api.get_song_detail(dict(ID = ids))['songs']
    musicOtp = []
    for i in range(len(ids)):
        mu = musicUrl[i]
        for mi in musicInfo:
            if mi['id'] == mu['id']:
                name = mi['name'] + " " + mi['alia'][0] if mi['alia'] else mi['name']
                artist = [ar['name'] for ar in mi['ar']]
                artistId = [ar['id'] for ar in mi['ar']]
                album = mi['al']['name']
                albumId = mi['al']['id']
                picUrl = mi['al']['picUrl']
                info = dict(name = name, artist = artist, album = album, picUrl = picUrl, artistId = artistId, albumId = albumId)
                musicInfo.remove(mi)
                break
        musicOtp.append(Music(mu["id"], mu["url"], mu["level"], mu["size"], mu["type"], info))
    if len(musicUrl) == 1:
        return musicOtp[0]
    return musicOtp

    # musicOtp = []
    # info = {"name": "","artist": "","album": ""}
    # musicOtp = []
    # for d in data:
    #     # if detail:
    #     #     info = query.getSongInfo(d["id"])
    #     # if not info:
    #     #     print("歌曲不存在 id=" + str(d["id"]))
    #     #     continue
    #     musicOtp.append(Music(d["id"], d["url"], d["level"], d["size"], d["type"], info))
    #     if len(data) == 1:
    #         return musicOtp[0]
    



class Music:
    def __init__(self, id_, url, level, size, type_, info):
        self.url = url
        self.id = str(id_)
        self.level = level
        self.size = int(size)
        self.type = type_
        self.name = info['name']
        self.artist =  info['artist']
        self.album = info['album']
        self.artistId = info['artistId']
        self.albumId = info['albumId']
        self.picUrl = info['picUrl']
        self.para = {
            "clas" : "",
            "ID" : self.id,
            "number" : 15,
            "offset" : 0,
        }
        self.levels = ["standard", "higher", "exhigh", "lossless"]


    def __repr__(self):
        return "<Music object - "+ self.id +">"

    def download(self, dirs="", level="standard"):
        if self.type:
            if level == "standard":
                return download.download(dirs, self)
            elif level in self.levels:
                return createObj([self.id], level).download()
            else:
                print("没有这个level, 默认standard")
                return download.download(dirs, self)
        else:
            print("download failed - " + self.id)
            return None

    # 获取评论数量
    def getCommentsCount(self):
        self.para["clas"] = "count"
        with sessions.Session() as session:
            return session.comment(self.para)

    # 获取热评，上限15
    def getHotComments(self, number=15):
        self.para["clas"] = "hot"
        self.para["number"] = number
        with sessions.Session() as session:
            return session.comment(self.para)
    
    # 获取评论，时间顺序，从最近的一直向后
    def getComments(self, number):
        self.para["clas"] = "new"
        self.para["number"] = str(number)
        with sessions.Session() as session:
            return session.comment(self.para)

    # 获取歌词
    def getLyrics(self):
        lrc =  api.Api().get_lyrics(dict(ID = self.id))
        lyric = lrc["lrc"]["lyric"]
        tlyric = lrc["tlyric"]["lyric"]
        return [lyric, tlyric]

