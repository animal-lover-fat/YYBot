from pywinauto.keyboard import send_keys


window = None


# 自定义发送信息
def SendMessages(messages):
    global window
    if window.is_minimized():  # 2. 如果最小化就恢复
        window.restore()
    text_elements = window.descendants(control_type="Pane")
    text_elements[3].type_keys(messages, with_spaces=True)
    send_keys("{ENTER}")

# 发送菜单
def SendMenu():
    messages = (
        "┌────────────────────────┐^{ENTER}"
        "┊　　　　  逆山不智能音乐播放器帮助菜单  　　　　┊^{ENTER}"
        "├————————————————————————┤^{ENTER}"
        "┊   数字 0/菜单指令帮助    数字 1/当前播放歌曲   ┊^{ENTER}"
        "┊   数字 2/暂停/继续  　   数字 3/上一首         ┊^{ENTER}"
        "┊   数字 4/下一首/切歌　　 数字 5/点歌列表    　 ┊^{ENTER}"
        "┊   帮助:菜单指令帮助      点歌列表:显示点歌列表 ┊^{ENTER}"
        "┊   读：XXX                             　　　　 ┊^{ENTER}"
        "┊   点歌功能：点歌歌名-歌手（QQ音乐）　　　　　　┊^{ENTER}"
        "└────────────────────────┘"
    )
    SendMessages(messages)

def SendNoSong():
    messages = "抱歉，没有找到音乐"
    SendMessages(messages)

def SendNoPreviousSong():
    messages = "抱歉，没有上一首"
    SendMessages(messages)

def SendSongListToYY(list):
    messages = ""
    number = 1
    for i in list:
        messages = messages + str(number) + "、" + i["name"] + "-" + i["singer"] + "^{ENTER}"
        number += 1
    SendMessages(messages)