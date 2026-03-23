import asyncio
import json
import os

from qqmusic_api.login import (
    QR,
    LoginError,
    QRCodeLoginEvents,
    QRLoginType,
    check_mobile_qr,  # [新增] 导入 check_mobile_qr
    check_qrcode,
    get_qrcode,
)

# from qqmusic_api import Credential


def show_qrcode(qr: QR):
    """显示二维码"""
    try:
        from io import BytesIO

        from PIL import Image
        from pyzbar.pyzbar import decode # type: ignore
        from qrcode import QRCode  # type: ignore

        img = Image.open(BytesIO(qr.data))
        decoded = decode(img)
        if not decoded:
            print("无法解码二维码图片")
            return

        url = decoded[0].data.decode("utf-8")
        qr_console = QRCode()
        qr_console.add_data(url)
        qr_console.print_ascii()
    except ImportError:
        # 保存二维码到当前目录
        save_path = qr.save()
        print(f"二维码已保存至: {save_path}")
        return save_path


async def qrcode_login_example(login_type: QRLoginType):  # noqa: C901
    """二维码登录示例"""

    try:
        # 1. 获取二维码
        print(f"正在获取 {login_type.name} 二维码...")
        qr = await get_qrcode(login_type)
        print(f"获取 {login_type.name} 二维码成功")

        image_path = show_qrcode(qr)

        # 2. 监听扫码状态
        # 注意: MOBILE (QQ音乐APP) 使用 MQTT 协议 (推送流), 其他使用 HTTP 协议 (轮询)

        if login_type == QRLoginType.MOBILE:
            print(">>> 请使用 [QQ音乐APP] 扫码 (MQTT监听中)")
            async for event, credential in check_mobile_qr(qr):
                print(f"当前状态: {event.name}")

                if event == QRCodeLoginEvents.DONE:
                    print(f"登录成功! MusicID: {credential.musicid}")
                    return credential

                elif event == QRCodeLoginEvents.TIMEOUT:
                    print("二维码已过期,请重新获取")
                    break

                elif event == QRCodeLoginEvents.REFUSE:
                    print("用户拒绝了登录请求")
                    break

                # MQTT 不需要 sleep,因为是服务器推送消息

        else:
            print(f">>> 请使用 [{login_type.name}] 扫码 (HTTP轮询中)")
            while True:
                event, credential = await check_qrcode(qr)
                print(f"当前状态: {event.name}")

                if event == QRCodeLoginEvents.DONE:
                    print(f"登录成功! MusicID: {credential.musicid}")
                    print(credential.as_json())
                    return credential

                if event == QRCodeLoginEvents.TIMEOUT:
                    print("二维码已过期,请重新获取")
                    break

                if event == QRCodeLoginEvents.SCAN:
                    await asyncio.sleep(3)  # 3秒轮询一次
                else:
                    await asyncio.sleep(2)
        
    except LoginError as e:
        print(f"登录失败: {e!s}")
    except Exception:
        raise
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)
            print("二维码图片已删除")

# 保存credential的数据
def SaveCredential(credential):
    data = credential.__dict__
    with open('CredentialData.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def QQMusicLogin():
    print("请选择登录方式:")
    print("1. QQ   (使用手机QQ扫码)")
    print("2. WX   (使用微信扫码)")
    print("3. MOBILE (使用QQ音乐APP扫码)")

    choice = input("请输入选项 (1/2/3): ").strip()

    if choice == "1":
        res = await qrcode_login_example(QRLoginType.QQ)
    elif choice == "2":
        res = await qrcode_login_example(QRLoginType.WX)
    elif choice == "3":
        res = await qrcode_login_example(QRLoginType.MOBILE)
    else:
        print("无效的选项")
    print(res)
    SaveCredential(res)

if __name__ == "__main__":
    try:
        asyncio.run(QQMusicLogin())
    except KeyboardInterrupt:
        print("\n用户取消操作")