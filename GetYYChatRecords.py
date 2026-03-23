import json
import time
import threading
import asyncio

from QQMusicApi import OrderQueue, ImportSongList
from datetime import datetime
from SendYYMessages import SendMenu, SendNoPreviousSong
from MusicPlayer import SendCurrentPlayingSong, PausePlayMusic, UnpausePlayMusic, NextMusic, PreviousMusic, SendSongList, ReduceVolume, IncreaseVolume, SetVolume
from Read import Read


RuningState = True
IsPause = True


# 获取YY语音聊天记录
def GetYYChatRecords(window):
        # 获取YY聊天记录
        text_elements = window.descendants(control_type="Text") # 获取窗口所有子元素的文本
        all_texts = []
        for elem in text_elements:
            try:
                text = elem.window_text()   # elem.window_text()：获取控件的文本内容
                all_texts.append(text)
            except:
                print("提取聊天记录出错")
        return ParseYYChatRecords(all_texts)

# 解析聊天记录
def ParseYYChatRecords(texts):
    chats = []
    current_chat = {}
    texts_len = len(texts)
    for i in range(texts_len-7):
        if texts[i+2] == '\xa0':
            if (texts[i+6] == '\xa0') and (texts[i+7] == '\n'):
                current_chat = {
                    "user_id":texts[i+1][1:-1], # 去除id的括号
                    "username":texts[i],
                    "time":texts[i+3],
                    "content":texts[i+5]
                }
                chats.append(current_chat)
    return chats

# 保存聊天记录
def SaveYYChatRecords(chats):
    if not chats:
        print("没有聊天记录可保存")
        return
    
    # 准备保存的数据
    save_data = {
        "export_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_messages":len(chats),
        "chat_history_content":[]
    }
    fileName = "yy_chat_history_"+datetime.now().isoformat()+".json"

    for chat in chats:
        chat_data = chat.copy()
        # 添加导出时间戳
        chat_data["exported_at"] = datetime.now().isoformat()
        save_data["chat_history_content"].append(chat_data)
    
    with open(fileName, 'w', encoding="utf-f") as file:
        json.dump(save_data, file, ensure_ascii=False, indent=2)

    print(f"聊天记录已保存到{fileName}")
    
    return True

# 实时监控聊天记录    
def MonitorYYChatInRealtime(window, interval):
    print(f"开始实时监控聊天记录，间隔{interval}秒...")

    all_chats = []
    last_count = 0
    iteration = 1
    global RuningState

    try:
        while RuningState:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]第 {iteration} 次检查...")
            chats = GetYYChatRecords(window)
            # print(f"\n[{datetime.now().strftime('%H:%M:%S')}]第 {iteration} 次检查...")
            if chats:
                if last_count < len(chats):
                    new_chats = chats[last_count:]
                    last_count = len(chats)
                elif last_count > len(chats):
                    all_chats = []
                    new_chats = chats
                else:
                    new_chats = []
                if new_chats:
                    # print(f"发现 {len(new_chats)} 条新消息：")
                    if iteration == 1:
                        all_chats.extend(new_chats)
                        time.sleep(interval)
                        iteration = iteration + 1
                        continue
                    for chat in new_chats:
                        # print(chat['content'])
                        if chat['content'] == "0" or chat['content'] == "帮助":
                            # print("菜单指令帮助")
                            # 菜单帮助指令
                            SendMenu()
                        elif chat['content'] == "1":
                            # 查询当前播放歌曲
                            SendCurrentPlayingSong()
                        elif chat['content'] == "2":
                            print("2")
                            # 暂停/继续
                            global IsPause
                            if IsPause:
                                PausePlayMusic()
                                IsPause = False
                            else:
                                UnpausePlayMusic()
                                IsPause = True    
                        elif chat['content'] == "3" or chat["content"] == "上一首":
                            print("3")
                            # 上一首
                            res = PreviousMusic()
                            if not res:
                                SendNoPreviousSong()
                        elif chat['content'] == "4" or chat['content'] == "下一首":
                            print("4")
                            # 下一首/切歌
                            NextMusic()
                        elif chat['content'] == "5" or chat['content'] == "查询点歌列表" or chat['content'] == "显示点歌列表":
                            print("5")
                            # 查询点歌列表
                            SendSongList()
                        elif chat['content'].startswith("读"):
                            print("读")
                            read = chat['content'][1:].strip()
                            print(read)
                            asyncio.run(Read(read))
                        elif chat['content'].startswith("点歌"):
                            # print("点歌")
                            song = chat['content'][2:].strip()
                            print(song)
                            OrderQueue.put(song)
                        elif chat['content'].startswith('设置音量'):
                            volume = chat['content'][4:].strip()
                            SetVolume(volume)
                            print("设置音量", volume)
                        elif chat['content'].startswith('音量+'):
                            step = chat["content"][3:].strip()
                            IncreaseVolume(step)
                            print("音量+",step)
                        elif chat['content'].startswith('音量-'):
                            step = chat["content"][3:].strip()
                            ReduceVolume(step)
                            print("音量-",step)
                        elif chat['content'].startswith("导入歌单"):
                            songlist_id = chat["content"][4:].strip()
                            ImportSongList(songlist_id)
                            print("导入歌单", songlist_id)
                all_chats.extend(new_chats)
            time.sleep(interval)
            iteration = iteration + 1
    except KeyboardInterrupt:
        print("\n监控已停止")
    finally:
        print("监控已停止")

def StopGetYYChatRecords():
    global RuningState
    RuningState = False
    # print("监控已停止")

def StartGetYYChatRecordsThread(window, interval):
    GetRecordsThread = threading.Thread(target=MonitorYYChatInRealtime, args=(window,interval,),)
    GetRecordsThread.start()
    return GetRecordsThread