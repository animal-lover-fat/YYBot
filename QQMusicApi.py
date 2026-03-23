import asyncio
import difflib
import json
import threading
import queue
import time
import os

from qqmusic_api import Credential, search, song, songlist, top, sync
from Login import QQMusicLogin
from MusicPlayer import MusicQueue
from SendYYMessages import SendNoSong
from qqmusic_api.song import SongFileType


OrderQueue = queue.Queue()
MusicList = []
RuningState = True
IsImportSongList = False
credential = None

# QQMusicApi官网：https://l-1124.github.io/QQMusicApi/
def GetCredentialData():
    global credential

    if os.path.isfile("CredentialData.json"):
        with open('CredentialData.json', 'r', encoding='utf-8') as f:
            CredentialData = json.load(f)
    else:
        print("CredentialData.json文件不存在")
        QQMusicLogin()

    credential = Credential(
        openid=CredentialData.get('openid'),
        refresh_token=CredentialData.get('refresh_token'),
        access_token=CredentialData.get('access_token'),
        expired_at=CredentialData.get('expired_at'),
        musicid=CredentialData.get('musicid'),
        musickey=CredentialData.get('musickey'),
        unionid=CredentialData.get('unionid'),
        str_musicid=CredentialData.get('str_musicid'),
        refresh_key=CredentialData.get('operefresh_keynid'),
        encrypt_uin=CredentialData.get('encrypt_uin'),
        login_type=CredentialData.get('login_type'),
        extra_fields=CredentialData.get('extra_fields')
    )

async def CheckCredential():
    # 判断 credential 是否过期
    is_expired = await credential.is_expired()
    # print(is_expired)
    return is_expired

# 点歌
def RequestSongByQQMusicApi(SongName,SingerName=None):
    # 查询歌曲信息
    SongList = sync(search.quick_search(SongName))['song']['itemlist']
    SongData = {}   # 用来传输的数据

    # 判断是否找到歌曲
    if len(SongList) == 0:
        return 0

    # 匹配歌手
    if SingerName:
        singers = []
        for item in SongList:
            singers.append(item['singer'])
        matches = difflib.get_close_matches(SingerName, singers, n=1, cutoff=0.2)
        if matches:
            for item in SongList:
                if item['singer'] == matches[0]:
                    urls = GetSongByMid(item['mid'])
                    SongData = item.copy()
                    SongData.update(url=urls[item['mid']])
    else:
        urls = GetSongByMid(SongList[0]['mid'])
        SongData = SongList[0]
        SongData.update(url=urls[SongList[0]['mid']])
    
    # 向播放器发送歌曲信息
    return SongData
    

# 通过mid获取播放路径
def GetSongByMid(mid):
    urls = asyncio.run(song.get_song_urls(mid=[mid], file_type=SongFileType.MP3_320, credential=credential))
    return urls
    
# 获取热歌榜
def GetHotSongList():
    global MusicList
    detail = asyncio.run(top.get_detail(top_id=26, num=50))
    MusicList = MusicList + detail['data']['song']
    print(MusicList)

# 获取歌名和歌手
def GetSongNameAndSinger(order):
    if '-' in order:
        parts = order.split('-', 1)
        SongName = parts[0]
        SingerName = parts[1]
        return SongName, SingerName
    else:
        return order, None

# 获取点歌信息
def GetOrder():
    global OrderQueue
    # global MusicList
    while RuningState:
        if not OrderQueue.empty():
            order = OrderQueue.get()
            # print(order)
            SongName, SingerName = GetSongNameAndSinger(order)
            SongData = RequestSongByQQMusicApi(SongName, SingerName)
            if not SongData:
                print('没找到歌曲')
                SendNoSong()
                continue
            # print(SongData)
            MusicQueue.put(SongData)
            time.sleep(1)
        time.sleep(1)

# 导入歌单
def ImportSongList(songlist_id):
    global MusicList, IsImportSongList
    list = asyncio.run(songlist.get_songlist(songlist_id))
    MusicList = list
    IsImportSongList = True

# 播放歌单（当没有歌曲时播放一首热歌榜的歌）
def PlaySongList():
    global MusicList, IsImportSongList
    if MusicList == []:
        IsImportSongList = False
        GetHotSongList()
    order = MusicList[0]
    if IsImportSongList:
        SongName = order['title']
        SingerName = order['singer'][0]['name']
    else:
        SongName = order['title']
        SingerName = order['singerName']
    SongData = RequestSongByQQMusicApi(SongName, SingerName)
    print(SongData)
    if not SongData:
        print("没找到歌曲")
        SendNoSong
    del MusicList[0]
    MusicQueue.put(SongData)

# 停止线程
def StopQQMusicApi():
    global RuningState
    RuningState = False 

# 启动线程
def StratQQMusicApi():
    GetOrder()
    print("QQMusicApi已停止")

# 创建线程
def StratQQMusicApiThread():
    QQMusicApiThread = threading.Thread(target=StratQQMusicApi)
    QQMusicApiThread.daemon = True
    QQMusicApiThread.start()
    return QQMusicApiThread