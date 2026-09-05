import os
import sqlite3
import datetime
import requests
import platform
from dotenv import load_dotenv
from pathlib import Path

# ---------- 1. 加载环境变量 ----------
script_dir = Path(__file__).parent
load_dotenv(script_dir / '.env')

# ---------- 2. 读取 PushPlus Token ----------
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")

# ---------- 3. 初始化弹窗（仅 Windows 可用） ----------
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 根据操作系统决定是否启用桌面弹窗
if platform.system() == "Windows":
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        print("✅ 桌面弹窗已启用 (Windows)")
    except ImportError:
        toaster = None
        print("⚠️ win10toast 未安装，桌面弹窗不可用")
else:
    toaster = None
    print(f"ℹ️ 当前系统为 {platform.system()}，桌面弹窗已禁用（仅保留微信推送）")

# ---------- 4. 手机推送函数 ----------
def send_pushplus(title, message):
    """通过 PushPlus 发送消息到微信"""
    if not PUSHPLUS_TOKEN:
        print("⚠️ 未配置 PUSHPLUS_TOKEN，跳过微信推送")
        return
    try:
        url = f"http://www.pushplus.plus/send?token={PUSHPLUS_TOKEN}&title={title}&content={message}"
        requests.get(url, timeout=5)
        print(f"📱 微信推送已发送: {title}")
    except Exception as e:
        print(f"⚠️ 微信推送失败（不影响主流程）: {e}")

# ---------- 5. 桌面通知函数（兼容 Linux） ----------
def send_desktop_notification(title, message):
    """发送桌面通知（Windows 弹窗，Linux 打印日志）"""
    if toaster:
        try:
            toaster.show_toast(title, message, duration=10, threaded=True)
            print(f"💻 [桌面弹窗] {message}")
        except Exception as e:
            print(f"⚠️ 桌面弹窗失败: {e}")
    else:
        # Linux 或未安装 win10toast 时，降级为打印
        print(f"💻 [桌面通知(模拟)] {message}")

# ---------- 6. 主提醒函数 ----------
def check_and_remind():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    
    now = datetime.datetime.now()
    future = now + datetime.timedelta(hours=24)
    
    rows = c.execute("SELECT id, event, due_date, due_time FROM tasks WHERE reminded = 0").fetchall()
    
    for row in rows:
        task_id, event, date, time = row
        due_str = f"{date} {time}"
        try:
            due_dt = datetime.datetime.strptime(due_str, "%Y-%m-%d %H:%M")
        except ValueError:
            due_dt = datetime.datetime.strptime(f"{date} {time}:00", "%Y-%m-%d %H:%M:%S")
        
        # 判断提醒类型
        if now <= due_dt <= future:
            message = f"📢 任务「{event}」即将在 {due_str} 截止！"
            # 桌面通知（兼容 Linux）
            send_desktop_notification("DDL 提醒器", message)
            # 微信推送
            send_pushplus("DDL 即将到期", message)
            c.execute("UPDATE tasks SET reminded = 1 WHERE id = ?", (task_id,))
            print(f"⏰ 已提醒（即将到期）: {event}")
            
        elif due_dt < now:
            message = f"🚨 任务「{event}」原定于 {due_str} 截止，已经过期！"
            # 桌面通知（兼容 Linux）
            send_desktop_notification("DDL 提醒器", message)
            # 微信推送
            send_pushplus("DDL 已过期", message)
            c.execute("UPDATE tasks SET reminded = 1 WHERE id = ?", (task_id,))
            print(f"⏰ 已提醒（已过期）: {event}")
        else:
            print(f"⏳ {event} 截止于 {due_str}，不在24小时内，暂不提醒")
    
    conn.commit()
    conn.close()
    print("✅ 检查完成")

if __name__ == "__main__":
    check_and_remind()