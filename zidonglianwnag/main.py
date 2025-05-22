import subprocess
import time
from threading import Thread
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image
import os
import sys

# ==== 直接在这里填写你的网络信息 ====
TARGET_SSID = "ChinaNet-0857-5G"
PASSWORD = "147258369"

# 检测间隔时间（单位：秒），15分钟=900秒
CHECK_INTERVAL = 900

# 重试间隔时间（单位：秒）
RETRY_INTERVAL = 5

def print_message(message):
    # 空操作，不再打印任何消息到控制台
    pass

def connect_to_wifi_windows(ssid, password):
    config = f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>
"""
    profile_path = f"{ssid}.xml"
    with open(profile_path, "w", encoding="utf-8") as f:
        f.write(config)
    subprocess.run(["netsh", "wlan", "add", "profile", f"filename={profile_path}"], stdout=subprocess.DEVNULL)
    subprocess.run(["netsh", "wlan", "connect", f"name={ssid}"], stdout=subprocess.DEVNULL)

def is_connected_windows(ssid):
    try:
        output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"]).decode("gbk")
        for line in output.split('\n'):
            if "SSID" in line and "BSSID" not in line:  # 排除其他包含SSID的行（如BSSID）
                current_ssid = line.split(":")[1].strip()
                if current_ssid == ssid:
                    return True
        return False
    except Exception as e:
        print_message(f"检查网络连接状态时发生错误: {e}")
        return False

def on_exit(icon, item):
    print_message("正在退出程序...")
    icon.stop()  # 停止托盘图标
    os._exit(0)  # 强制退出整个程序

def create_tray_icon():
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "tubiao.ico")
        print_message(f"图标文件路径: {icon_path}")
        if not os.path.exists(icon_path):
            print_message("警告：图标文件不存在")
        image = Image.open(icon_path)
        print_message("✅ 成功加载系统托盘图标。")
    except Exception as e:
        print_message(f"❌ 加载图标失败: {e}")
        image = Image.new('RGB', (64, 64), color=(73, 109, 173))  # 默认图标

    tray_menu = menu(item('退出', on_exit))
    icon_tray = icon("自动联网", image, "联网助手", tray_menu)
    icon_tray.run()

def main_program():
    print_message("自动连接守护程序已启动...")

    while True:
        print_message("正在检查网络连接状态...")

        if is_connected_windows(TARGET_SSID):
            status_message = f"当前已连接到 {TARGET_SSID}"
            print_message(status_message)
            print_message(f"下次检测将在 {CHECK_INTERVAL // 60} 分钟后进行。")
            time.sleep(CHECK_INTERVAL)
            continue
        else:
            # 进入循环重连模式
            print_message(f"当前未连接到 {TARGET_SSID}，开始尝试重新连接...")
            retry_count = 0
            while not is_connected_windows(TARGET_SSID):
                retry_count += 1
                print_message(f"第 {retry_count} 次尝试连接 {TARGET_SSID} ...")
                connect_to_wifi_windows(TARGET_SSID, PASSWORD)
                time.sleep(3)  # 给系统一点时间连接
                if is_connected_windows(TARGET_SSID):
                    print_message(f"✅ 成功连接到 {TARGET_SSID}，共尝试 {retry_count} 次")
                    break
                else:
                    print_message(f"❌ 连接失败，{RETRY_INTERVAL} 秒后再次尝试...")
                    time.sleep(RETRY_INTERVAL)

if __name__ == "__main__":
    # 启动系统托盘图标（作为守护线程）
    tray_thread = Thread(target=create_tray_icon, daemon=True)
    tray_thread.start()

    # 启动主程序逻辑
    main_program()