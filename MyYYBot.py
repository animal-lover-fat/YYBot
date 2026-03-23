import traceback
import SendYYMessages
import asyncio

from pywinauto import Application
from GetYYChatRecords import StartGetYYChatRecordsThread, StopGetYYChatRecords
from MusicPlayer import StartPlayMusicThread, StopPlayMusic
from QQMusicApi import StratQQMusicApiThread, StopQQMusicApi, CheckCredential, GetCredentialData
from Login import QQMusicLogin


window_title = "1463747850-养老"
YYWindow = None


def ConnectYYWindow(window_title):
    try:
        # 连接到窗口
        app = Application(backend="uia").connect(title=window_title, timeout=10)
        window = app.window(title=window_title)
        print(f"已连接到窗口: {window_title}")
        return window
    except Exception as exception:
        print(f"连接窗口失败：{exception}")
        traceback.print_exc()   # 打印完整的错误堆栈信息
        return False

def StartYYBot():
    # window_title = "1463747850-养老"
    # PowerShell获取窗口标题命令：Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object Name, MainWindowTitle
    window_title = input()
    YYWindow = ConnectYYWindow(window_title)
    SendYYMessages.window = YYWindow
    GetCredentialData()
    CheckResult = asyncio.run(CheckCredential())
    if CheckResult:
        asyncio.run(QQMusicLogin())
        GetCredentialData()
    GetRecordsThread = StartGetYYChatRecordsThread(YYWindow,interval=0.1)
    PlayMusicThread = StartPlayMusicThread()
    QQMusicApiThread = StratQQMusicApiThread()
    try:
        while True:
            command = input()
            if command == "exit":
                print("程序正在关闭")
                break
    except KeyboardInterrupt:
        print("\n收到 Ctrl+C")
    finally:
        StopGetYYChatRecords()
        StopPlayMusic()
        StopQQMusicApi()
        GetRecordsThread.join()
        PlayMusicThread.join()
        QQMusicApiThread.join()
        print("程序已关闭")


if __name__ == "__main__":
    StartYYBot()