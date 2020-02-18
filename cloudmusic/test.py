import cloudmusic
import time
import re
import urllib.request

# playlist = api.getSong(445702291)
# 601776277 是我的一个歌单id
# print(playlist)
# [<Music object - 445702291>, <Music object - 27198683>, <Music object - 27198679>, <Music object - 1868496>, <Music object - 26857076>, <Music object - 27198673>, <Music object - 27198672>, <Music object - 27198671>, <Music object - 1868520>, <Music object - 1868553>, <Music object - 486069583>, <Music object - 27198663>, <Music object - 1869285>, <Music object - 27198691>, <Music object - 1868483>]
# 每个Music object包含属性：url(音频文件链接)，level(品质)，tyoe(格式)，id(歌曲id)，name(歌曲名)，aitist(歌手)，album(所属专辑)，size(音频文件大小)
# 每个Music object包含方法：1.download()下载到本地   2.review()获取详细评论


# music = cloudmusic.getMusic(1381755293)

# print(music.getCommentCount())

# comments = music.getHotComments()

# for com in comments:
#     print(com['content'])
#     print(com['likeCount'])

user = cloudmusic.getUser(11898913)

print(user.getRecord(1))








# loader = api.createLoader()

# loader.data = musicList

# if __name__ == "__main__":
#     loader.start()











