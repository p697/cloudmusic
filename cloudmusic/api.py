from . import query
from . import encrypt

import json

class Api:

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36',
            'cookie': 'MUSIC_U=e4ace7b13afdd88161175bda1c091445ad6bc398f36fb0f0315f1fa0787d4fbce7c70899629a7e58dcb329764b52b00341049cea1c6bb9b6',
            'referer': 'https://music.163.com'
        }

    def send(self, url, param={}):
        return query.post(url,
                        self.headers,
                        encrypt.encrypted_request(param))

    def get_song_url(self, para):
        url = "https://music.163.com/weapi/song/enhance/player/url/v1"
        param = dict(ids = para["ID"], level = para["level"], encodeType = "aac")
        return self.send(url, param)


    def search(self,para):
        url = "https://music.163.com/weapi/cloudsearch/get/web"
        param = '{"hlpretag":"<span class=\\"s-fc7\\">","hlposttag":"</span>","s":"'+ para["string"] +'","type":"1","offset":"0","total":"true","limit":"'+ para["number"] +'","csrf_token":""}'
        return self.send(url, param)


    def get_commets(self,para):
        url = "https://music.163.com/weapi/v1/resource/comments/R_SO_4_{}".format(para["ID"])
        param = '{"rid":"R_SO_4_'+ para["ID"] +'","offset":"'+ para["offset"] +'","total":"'+ para["total"] +'","limit":"'+ para["limit"] +'","csrf_token":""}'
        return self.send(url, param)


    def get_lyrics(self,para):
        url = "https://music.163.com/weapi/song/lyric"
        param = '{"id":"'+ para["ID"] +'","lv":-1,"tv":-1,"csrf_token":""}'
        return self.send(url, param)


    def get_song_detail(self, para):
        url = "https://music.163.com/weapi/v3/song/detail"
        param = dict(c=json.dumps([{"id": _id} for _id in para["ID"]]), ids=json.dumps(para["ID"]))
        return self.send(url, param)


    def get_playlist(self, para):
        url = "https://music.163.com/weapi/v3/playlist/detail"
        param = dict(id=para["ID"], total="true", limit=1000, n=1000, offest=0)
        return self.send(url, param)


    def get_album(self, para):
        url = "https://music.163.com/weapi/v1/album/{}".format(para["ID"])
        return self.send(url)


    def get_userInfo(self, para):
        url = "https://music.163.com/api/v1/user/detail/{}".format(para["ID"])
        return self.send(url)


    def get_userPlayerlist(self, para):
        url = "https://music.163.com/weapi/user/playlist"
        params = dict(uid=para["ID"], wordwrap=7, offset=0, total="true", limit=1000)
        return self.send(url, params)


    def get_userRecord(self, para):
        url = "https://music.163.com/weapi/v1/play/record"
        params = dict(uid=para["ID"], type=-1, limit=1000, offset=0, total="true")
        return self.send(url, params)


    


