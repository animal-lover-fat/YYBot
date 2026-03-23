# YYBot
YY语音播放器

# 简介
此项目用于在YY语音播放音乐，有点歌、导入歌单、打印提示、读出公屏文字的功能，但目前音乐api仅支持QQ音乐歌曲。

# 快速开始
## 环境要求
- 3.10 =< python < 3.14
- pygame
- qqmusic-api-python，详情见https://github.com/l-1124/QQMusicApi
- pywinauto
- edge_tts
## 基本使用
MyYYBot为本项目的入口文件，运行该文件并按照控制台的提示登录QQ音乐的账号，然后输入YY语音房间窗口的标题（YY房间号-YY房间名称）。  注意不能最小化YY窗口，并且需要点击一下YY的输入框否则播放器的打字功能会无法使用。播放器会自动获取YY公屏信息来进行点歌。
## 点歌功能
在YY公屏输入点歌xx（歌名）
## 导入歌单
在YY公屏输入点导入歌单xx（歌单的id）
## 阅读功能
在YY公屏输入读xx（内容）

# 注意
- 本项目需要有QQ音乐的账号登录，并且VIP歌曲无法免费播放，本质上就是登录你的账号去官网请求音乐。
- 账号登录后的凭证会被保存在CredentialData.json文件中请妥善保管。

# License
本项目基于 MIT License 许可证发行。