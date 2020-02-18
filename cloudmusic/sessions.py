from . import encrypt
from . import query
from . import download
from . import api
from . import musicObj
from . import userObj



class Session():
    def __init__(self):

        self.error = "错误参数 --- 运行cloudmusic.help()查看支持"

        self.api = api.Api()

        # 默认音质
        self.level = "higher"


    def __enter__(self):
        return self


    def __exit__(self, *args):
        pass


    def request(self, clas, para):
        # 先判断数据是否合法
        if isinstance(para, list):
            try:
                ids = [int(p) for p in para]
            except:
                return self.error
        else:
            try:
                ids = [int(para)]
            except:
                return self.error


        if clas == "song":
            return musicObj.createObj(ids, self.level)

        # 歌单                        
        elif clas == "playlist" :
            playlist = self.api.get_playlist(dict(ID = ids[0]))["playlist"]["tracks"]
            ids = [ml["id"] for ml in playlist]
            musicList = self.request("song", ids)
            musicListc = []
            for ID in ids:
                for music in musicList:
                    if music.id == str(ID):
                        musicListc.append(music)
                        musicList.remove(music)
                        continue
            return musicListc
    
        # 专辑
        elif clas == "album":
            playlist = self.api.get_album(dict(ID = ids[0]))["songs"]
            ids = [ml["id"] for ml in playlist]
            musicList = self.request("song", ids)
            musicList = [musicList] if len(ids) == 1 else musicList
            musicListc = []
            for ID in ids:
                for music in musicList:
                    if music.id == str(ID):
                        musicListc.append(music)
                        musicList.remove(music)
                        continue
            return musicListc

        # 用户
        elif clas == "user":
            return userObj.createUser(ids[0])

        else :
            return self.error


    # 搜索
    def search(self, content, number):
        para = {
            "string" : str(content),
            "number" : str(number)
        }
        ids = self.api.search(para)
        
        musicList = self.request("song", ids)
        musicList = [musicList] if not isinstance(musicList, list) else musicList
        musicListc = []
        for ID in ids:
            for music in musicList:
                if music.id == str(ID):
                    musicListc.append(music)
                    musicList.remove(music)
                    continue
        return musicListc


    # 评论
    def comment(self, mpara):
        para = {
            "ID" : mpara["ID"],
            "offset" : "0",
            "total" : "true",
            "limit" : "20"
        }
        if mpara["clas"] == "count":
            return self.api.get_commets(para)["total"]
        if mpara["clas"] == "hot":
            comments = self.api.get_commets(para)["hotComments"]
            return self.datalizeComment(comments, mpara["number"])
        if mpara["clas"] == "new":
            offset = 0
            number = int(mpara["number"])
            comments = []
            for _ in range(int(number / 20)):
                para["offset"] = str(offset)
                para["limit"] = str(offset + 20)
                comments.extend(self.api.get_commets(para)["comments"])
                offset += 20
            para["offset"] = str(offset)
            para["limit"] = str(number - int(number / 20) * 20)
            comments.extend(self.api.get_commets(para)["comments"])
            return self.datalizeComment(comments, mpara["number"])


    # 评论格式化
    def datalizeComment(self, comments, number):
        number = len(comments) if int(number) > len(comments) else int(number)
        comList = []
        for com in comments[0:number]:
            comDic = dict( likeCount = com['likedCount'], 
                        content = com['content'],
                        time = com['time'],
                        nickName = com['user']['nickname'],
                        userId = str(com['user']['userId']),
                        avatarUrl = com['user']['avatarUrl'],
                        vipType = com['user']['vipType'],
                        userType = com['user']['userType']
                        )
            comList.append(comDic)
        return comList
        

    # 多进程下载
    def downloader(self, procs, dirs):
        return download.Downloader(procs, dirs)
        
    

        


