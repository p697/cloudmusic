from . import query
from . import api
from . import sessions


def createUser(ID):
    info = api.Api().get_userInfo(dict(ID = ID))
    return User(info)


class User:
    def __init__(self, info):
        self.id = str(info['userPoint']['userId'])
        self.level = info['level']
        self.sex = info['profile']['gender']
        self.listenSongs = info['listenSongs']
        self.createTime = info['profile']['createTime']
        self.nickname = info['profile']['nickname']
        self.avatarUrl = info['profile']['avatarUrl']
        self.city = info['profile']['city']
        self.province = info['profile']['province']
        self.vipType = info['profile']['vipType']
        self.birthday = info['profile']['birthday']
        self.signature = info['profile']['signature']
        self.fans = info['profile']['followeds']
        self.follows = info['profile']['follows']
        self.eventCount = info['profile']['eventCount']
        self.playlistCount = info['profile']['playlistCount']


    def getPlaylist(self):
        info = api.Api().get_userPlayerlist(dict(ID = self.id))['playlist']
        outp = []
        for pl in info:
            playlist = dict(
                id = pl['id'],
                creatorId = pl['userId'],
                playCount = pl['playCount'],
                createTime = pl['createTime'],
                coverImgUrl = pl['coverImgUrl'],
                name = pl['name'],
                updateTime = pl['updateTime'],
                tags = pl['tags']
            )
            outp.append(playlist)
        return outp


    def getRecord(self, recordType=0):
        info = api.Api().get_userRecord(dict(ID = self.id))
        if info['weekData']:
            weekIds = [wd['song']['id'] for wd in info['weekData']]
            weekObj = sessions.Session().request("song", weekIds)
            weekOtp = []
            for wi in range(len(weekIds)):
                weekOtp.append(dict(score = info['weekData'][wi]['score'], music = weekObj[wi]))
        else:
            weekOtp = []

        if info['allData']:
            allIds = [ad['song']['id'] for ad in info['allData']]
            allObj = sessions.Session().request("song", allIds)
            allOtp = []
            for ai in range(len(allIds)):
                allOtp.append(dict(score = info['allData'][ai]['score'], music = allObj[ai]))
        else:
            allOtp = []

        if recordType:
            return weekOtp
        else:
            return allOtp


