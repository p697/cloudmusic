from . import musicObj
from . import api

import requests
import json
from lxml import etree
import time
import re



def post(url, headers, data):
    res = requests.post(url=url, headers=headers, data=data)

    if res.status_code == 200:
        if not res.text:
            return "请求出错"

        if "cloudsearch" in url:
            ids = []
            for li in json.loads(res.text)['result']['songs']:
                ids.append(li["id"])
            return ids
        else:
            # print(res.text)
            return json.loads(res.text)
    else:
        return "请求出错"


# 老方法获取用户信息
def getUserInfo(ID):
    url='https://music.163.com/user/home?id={}'.format(ID)
    session = requests.Session()
    session.headers = api.Api().headers
    res = session.get(url)

    html = etree.HTML(res.text)
    name = html.xpath('//*[@id="j-name-wrap"]/span[1]')[0].text
    level = html.xpath('//*[@id="j-name-wrap"]/span[3]')[0].text
    sexText = etree.tostring(html.xpath('//*[@id="j-name-wrap"]/i')[0]).decode("utf-8")
    if sexText.split('"/>')[-2:] == '01':
        sex = "male"
    elif sexText.split('"/>')[-2:] == '02':
        sex = "female"
    else:
        sex = None
    eventCount = html.xpath('//*[@id="event_count"]')[0].text
    followCount = html.xpath('//*[@id="follow_count"]')[0].text
    fanCount = html.xpath('//*[@id="fan_count"]')[0].text
    musicCount = re.split("歌|首", html.xpath('//*[@id="rHeader"]/h4')[0].text)[1]
    createdCount = re.split("（|）", html.xpath('//*[@id="cHeader"]/h3/span/text()[2]')[0])[1]
    collectCount = re.split("（|）", html.xpath('//*[@id="sHeader"]/h3/span/text()[2]')[0])[1]

    avatarUrl = html.xpath('//*[@id="ava"]/img')[0].get("src")

    div2 = html.xpath('//*[@id="head-box"]/dd/div[2]')
    if div2:
        if "个人介绍" in div2[0].text:
            print("是个人介绍")
            print(div2[0].text)
            # if html.xpath('//*[@id="head-box"]/dd/div[3]/span[1]') and not html.xpath('//*[@id="age"]/span'):
            #     print("有介绍和地区")
            #     print(html.xpath('//*[@id="head-box"]/dd/div[3]/span[1]')[0].text)
            # elif html.xpath('//*[@id="head-box"]/dd/div[3]/span[1]'):
            #     print("有介绍和年龄")
            #     print(html.xpath('//*[@id="age"]/span')[0].text)
            if html.xpath('//*[@id="head-box"]/dd/div[3]/span[1]') and html.xpath('//*[@id="age"]/span'):
                print("三个搜有")
                print(etree.tostring(html.xpath('//*[@id="age"]')[0]))
                print(html.xpath('//*[@id="head-box"]/dd/div[3]/span[1]')[0].text)
        else:
            print("是地区")
            a = html.xpath('//*[@id="head-box"]/dd/div[2]/span[1]')[0].text
            print(a)

    input()


    location = html.xpath('//*[@id="head-box"]/dd/div[3]/span[1]')
    location = location[0].text[5:] if location else None

    introduation = html.xpath('//*[@id="head-box"]/dd/div[2]')
    introduation = introduation[0].text[5:] if introduation else None
    
    age = html.xpath('//*[@id="age"]/span')
    age = age[0].text if age else None
    print(introduation)
    

    print(location)
    print(age)
    print(musicCount)

    input()


    title = html.xpath("/html/head/title")[0].text
    try:
        name = title.split(" -" )[0]
        artist = title.split(" - ")[1]
    except:
        return ""
    album = html.xpath("/html/body/div[3]/div[1]/div/div/div[1]/div[1]/div[2]/p[2]/a")[0].text
    info = {
        "name" : name,
        "artist" : artist,
        "album" : album,
    }
    
    return info


# 老方法获取歌曲详细信息
def getSongInfo(id_):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Referer': 'http://music.163.com/'
        }
    url='http://music.163.com/song?id=' + str(id_)
    session = requests.Session()
    session.headers=headers
    res = session.get(url)

    html = etree.HTML(res.text)
    title = html.xpath("/html/head/title")[0].text
    try:
        name = title.split(" -" )[0]
        artist = title.split(" - ")[1]
    except:
        return ""
    album = html.xpath("/html/body/div[3]/div[1]/div/div/div[1]/div[1]/div[2]/p[2]/a")[0].text
    info = {
        "name" : name,
        "artist" : artist,
        "album" : album,
    }
    print("creep --- " + str(id_))
    return info


# 老方法获取歌单信息
def getPlayList(id_):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Referer': 'http://music.163.com/'
        }
    url='http://music.163.com/playlist?id=' + str(id_)
    session = requests.Session()
    session.headers=headers
    res = session.get(url)

    html = etree.HTML(res.text)
    lists = html.xpath('//ul[@class="f-hide"]/li/a/@href')

    musicList = map(lambda x: x.split("=")[1], lists)
    
    return list(musicList)
