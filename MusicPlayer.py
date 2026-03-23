import pygame
import requests
import threading
import queue
import time
import os

from io import BytesIO
from SendYYMessages import SendMessages, SendSongListToYY


MusicQueue = queue.Queue()
MusicInfoList = [] 
RuningState = True
CurrentMusic = None
IsPause = False
CurrentMusicIndex = 0


# 播放音乐
def PlayMusic(url): 
    PlayThread = player.play(url)
    return PlayThread

# 上一首
def PreviousMusic():
    global CurrentMusic, MusicInfoList, CurrentMusicIndex
    # CurrentMusicIndex = MusicInfoList.index(CurrentMusic)
    CurrentMusicIndex = len(MusicInfoList) - 1 - MusicInfoList[::-1].index(CurrentMusic)
    if CurrentMusicIndex:
        PreviousMusicIndex = CurrentMusicIndex - 1
        CurrentMusic = MusicInfoList[PreviousMusicIndex]
        CurrentMusicIndex = PreviousMusicIndex
        PlayMusic(MusicInfoList[PreviousMusicIndex]['url'])
        return True
    else:
        return False

# 下一首
def NextMusic():
    global MusicInfoList, CurrentMusicIndex
    # print(CurrentMusicIndex < len(MusicInfoList)-1)
    if CurrentMusicIndex  < len(MusicInfoList)-1:
        CurrentMusicIndex = CurrentMusicIndex + 1
        PlayMusic(MusicInfoList[CurrentMusicIndex]['url'])
    else:
        player.stop()

# 暂停播放
def PausePlayMusic():
    global IsPause
    IsPause = True
    player.pause()

# 继续播放
def UnpausePlayMusic():
    global IsPause
    IsPause = False
    player.unpause()

# 停止线程
def StopPlayMusic():
    global RuningState
    RuningState = False
    player.stop()

# 设置音量
def SetVolume(volume):
    try:
        volume = int(volume)
        player.set_volume(volume/100)
    except ValueError:
        print("减小音量的参数转换成int类型时出错")
    except:
        print("减小音量出错")

# 减小音量
def ReduceVolume(step):
    try:
        volume = int(step)
        player.reduce_volume(volume/100)
    except ValueError:
        print("减小音量的参数转换成int类型时出错")
    except:
        print("减小音量出错")

# 增加音量
def IncreaseVolume(step):
    try:
        volume = int(step)
        player.increase_volume(volume/100)
    except ValueError:
        print("增加音量的参数转换成int类型时出错")
    except:
        print("增加音量出错")

def StartPlayMusic():
    from QQMusicApi import OrderQueue, PlaySongList
    global RuningState, CurrentMusicIndex
    
    while RuningState:
        try:
            # 非阻塞获取，避免卡死
            if not MusicQueue.empty():
                global MusicInfoList
                global CurrentMusic
                CurrentMusic = MusicQueue.get(timeout=1)
                MusicInfoList.append(CurrentMusic)
                CurrentMusicIndex = len(MusicInfoList) - 1
                # print(MusicInfoList)

                # 播放音乐
                PlayThread = PlayMusic(CurrentMusic['url'])
                
                # 等待播放结束或被停止
                PlayThread.join()
            else:
                PlaySongList()        
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ 播放线程错误: {e}")
    
    player.cleanup()
    print("🎵 音乐播放线程结束")

# YY公屏打印正在播放的音乐名称
def SendCurrentPlayingSong():
    messages = '当前正在播放：' + MusicInfoList[-1]['name'] + '-' + MusicInfoList[-1]['singer']
    SendMessages(messages)

# YY公屏打印点歌列表
def SendSongList():
    if not MusicQueue.empty():
        SongList = []
        SongList.append(CurrentMusic)
        SongList.extend(list(MusicQueue.queue))
        SendSongListToYY(SongList)
    elif CurrentMusic and MusicQueue.empty():
        messages = CurrentMusic['name'] + '-' + CurrentMusic['singer']
        SendMessages(messages)
    else:
        messages = "没有歌曲"
        SendMessages(messages)

# 创建线程
def StartPlayMusicThread():
    PlayMusicThread = threading.Thread(target=StartPlayMusic)
    PlayMusicThread.daemon = True
    PlayMusicThread.start()
    return PlayMusicThread


class StreamMusicPlayer:
    def __init__(self):
        self.is_playing = False
        self.current_url = None
        self.buffer = BytesIO()
        self.chunk_size = 4096
        self.volume = 0.2

        pygame.init()
        # pygame.mixer.init()
        # pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=1024)
        os.environ['SDL_AUDIODRIVER'] = 'wasapi'
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2)
        pygame.mixer.init()
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.set_num_channels(64)
        
    def stream_and_play(self, url):
        """从网络URL流式播放音乐"""
        try:
            print(f"开始播放: {url}")
            
            # 添加headers模拟浏览器请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://y.qq.com/',
                'Accept': 'audio/webm,audio/ogg,audio/wav,audio/*;q=0.9,application/ogg;q=0.7,video/*;q=0.6,*/*;q=0.5',
                'Accept-Encoding': 'identity;q=1, *;q=0',
                'Range': 'bytes=0-',  # 请求整个文件
            }
            
            # 发送HTTP请求获取音频流
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            
            # print(f"响应状态码: {response.status_code}")
            # print(f"响应头: {response.headers}")
            
            if response.status_code not in [200, 206]:
                print(f"无法获取音频流，状态码: {response.status_code}")
                return
                
            # 清空缓冲区
            self.buffer = BytesIO()
            
            # 写入音频数据到缓冲区
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if not self.is_playing:
                    break
                self.buffer.write(chunk)
            
            # 如果播放被停止，提前返回
            if not self.is_playing:
                return
                
            # 重置缓冲区位置并加载音乐
            self.buffer.seek(0)
            pygame.mixer.music.load(self.buffer)
            pygame.mixer.music.play()
            
            print("音乐开始播放")
            
            # 等待音乐播放完成
            while self.is_playing:
                # 播放完成自然退出
                if not pygame.mixer.music.get_busy() and not IsPause:
                    break
                time.sleep(2)
        except Exception as e:
            print(f"播放出错: {e}")
        finally:
            self.is_playing = False
            
    def play(self, url):
        """开始播放音乐"""
        if self.is_playing:
            self.stop()
            
        self.is_playing = True
        self.current_url = url
        
        # 在新线程中播放，避免阻塞主程序
        play_thread = threading.Thread(target=self.stream_and_play, args=(url,))
        play_thread.daemon = True
        play_thread.start()
        return play_thread
        
    def pause(self):
        """暂停播放"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            print("音乐已暂停")
            
    def unpause(self):
        """继续播放"""
        pygame.mixer.music.unpause()
        print("音乐继续播放")
        
    def stop(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.is_playing = False
        print("音乐已停止")
        
    def set_volume(self, volume):
        """设置音量"""
        pygame.mixer.music.set_volume(volume)

    def reduce_volume(self, step):
        """减小音量"""
        self.volume = self.volume - step
        if self.volume < 0:
            self.volume = 0
        self.set_volume(self.volume)

    def increase_volume(self, step):
        """增加音量"""
        self.volume = self.volume + step
        if self.volume > 1:
            self.volume = 1
        self.set_volume(self.volume)
        
    def cleanup(self):
        """清理资源"""
        self.stop()
        pygame.mixer.quit()
        pygame.quit()

player = StreamMusicPlayer()