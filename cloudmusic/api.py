from . import query
from . import encrypt

import json
import random


class Api:

    def __init__(self):
        self.userAgent = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
            "Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_2 like Mac OS X) AppleWebKit/603.2.4 (KHTML, like Gecko) Mobile/14F89;GameHelper",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0 like Mac OS X) AppleWebKit/602.1.38 (KHTML, like Gecko) Version/10.0 Mobile/14A300 Safari/602.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:46.0) Gecko/20100101 Firefox/46.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:46.0) Gecko/20100101 Firefox/46.0",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
            "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
            "Mozilla/5.0 (Windows NT 6.3; Win64, x64; Trident/7.0; rv:11.0) like Gecko",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/13.10586",
            "Mozilla/5.0 (iPad; CPU OS 10_0 like Mac OS X) AppleWebKit/602.1.38 (KHTML, like Gecko) Version/10.0 Mobile/14A300 Safari/602.1"
        ]
        musicU = 'e4ace7b13afdd88161175bda1c091445ad6bc398f36fb0f0315f1fa0787d4fbce7c70899629a7e58dcb329764b52b00341049cea1c6bb9b6'
        self.CookiesList = [
            'os=pc; osver=Microsoft-Windows-10-Professional-build-10586-64bit; appver=2.0.3.131777; channel=netease; __remember_me=true',
            'MUSIC_U=' + musicU + '; buildver=1506310743; resolution=1920x1080; mobilename=MI5; osver=7.0.1; channel=coolapk; os=android; appver=4.2.0',
            'osver=%E7%89%88%E6%9C%AC%2010.13.3%EF%BC%88%E7%89%88%E5%8F%B7%2017D47%EF%BC%89; os=osx; appver=1.5.9; MUSIC_U=' +
            musicU + '; channel=netease;'
        ]
        self.headers = {
            'User-Agent': random.choice(self.userAgent),
            'cookie': random.choice(self.CookiesList),
            'referer': 'https://music.163.com'
        }

    def send(self, url, param={}, method=''):
        return query.post(url,
                          self.headers,
                          encrypt.encrypted_request(param, method))

    def get_song_url(self, para):
        url = "https://music.163.com/weapi/song/enhance/player/url/v1"
        param = dict(ids=para["ID"], level=para["level"], encodeType="aac")
        return self.send(url, param)

    def search(self, para):
        url = "https://music.163.com/weapi/cloudsearch/get/web"
        param = '{"hlpretag":"<span class=\\"s-fc7\\">","hlposttag":"</span>","s":"' + \
            para["string"] + '","type":"1","offset":"0","total":"true","limit":"' + \
                para["number"] + '","csrf_token":""}'
        return self.send(url, param)

    def get_commets(self, para):
        url = "https://music.163.com/weapi/v1/resource/comments/R_SO_4_{}".format(
            para["ID"])
        param = '{"rid":"R_SO_4_' + para["ID"] + '","offset":"' + para["offset"] + \
            '","total":"' + para["total"] + '","limit":"' + \
                para["limit"] + '","csrf_token":""}'
        return self.send(url, param)

    def get_lyrics(self, para):
        url = "https://music.163.com/weapi/song/lyric"
        param = '{"id":"' + para["ID"] + '","lv":-1,"tv":-1,"csrf_token":""}'
        return self.send(url, param)

    def get_song_detail(self, para):
        url = "https://music.163.com/weapi/v3/song/detail"
        param = dict(c=json.dumps(
            [{"id": _id} for _id in para["ID"]]), ids=json.dumps(para["ID"]))
        return self.send(url, param)

    # 是个让人脑阔疼的api
    def get_playlist(self, para, method=""):
        url = "http://music.163.com/api/v3/playlist/detail"
        param = dict(id=para["ID"], total="true", limit=1000, n=1000, offest=0)
        return self.send(url, param, method=para["method"])

    def get_album(self, para):
        url = "https://music.163.com/weapi/v1/album/{}".format(para["ID"])
        return self.send(url)

    def get_userInfo(self, para):
        url = "https://music.163.com/api/v1/user/detail/{}".format(para["ID"])
        return self.send(url)

    def get_userPlayerlist(self, para):
        url = "https://music.163.com/weapi/user/playlist"
        params = dict(uid=para["ID"], wordwrap=7,
                      offset=0, total="true", limit=1000)
        return self.send(url, params)

    def get_userRecord(self, para):
        url = "https://music.163.com/weapi/v1/play/record"
        params = dict(uid=para["ID"], type=-1,
                      limit=1000, offset=0, total="true")
        return self.send(url, params)
