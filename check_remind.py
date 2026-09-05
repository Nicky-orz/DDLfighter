import os
import os
import sqlite3
import datetime
import requests
import platform
from pathlib import Path

# ---------- 1. 切换到脚本所在目录 ----------
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------- 2. 读取环境变量（本地用 .env，云端用 Secrets） ----------
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")

# 如果本地没有环境变量，尝试从 .env 文件加载（仅本地开发用）
if not PUSHPLUS_TOKEN:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")
    except ImportError:
        pass  # 云端没有 dotenv 也没关系

# ---------- 3. 初始化弹窗（仅 Windows） ----------
if platform.system() == "Windows":
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
    except ImportError:
        toaster = None
else:
    toaster = None

# ---------- 3. 手机推送函数 ----------
def send_pushplus(title, message):
    if not PUSHPLUS_TOKEN:
        print("⚠️ 未配置 PUSHPLUS_TOKEN，跳过微信推送")
        return
    try:
        url = f"http://www.pushplus.plus/send?token={PUSHPLUS_TOKEN}&title={title}&content={message}"
        requests.get(url, timeout=5)
        print(f"📱 微信推送已发送: {title}")
    except Exception as e:
        print(f"⚠️ 微信推送失败: {e}")

# ---------- 4. 桌面通知函数 ----------
def send_desktop_notification(title, message):
    if toaster:
        try:
            toaster.show_toast(title, message, duration=10, threaded=True)
            print(f"💻 [桌面弹窗] {message}")
        except Exception as e:
            print(f"⚠️ 桌面弹窗失败: {e}")
    else:
        print(f"💻 [桌面通知(模拟)] {message}")

# ---------- 5. 数据库初始化 ----------
def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            due_date TEXT NOT NULL,
            due_time TEXT NOT NULL,
            raw_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            reminded INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# ---------- 6. 主提醒函数 ----------
def check_and_remind():
    init_db()  # 确保表存在（如果数据库为空，会创建空表，查询返回空）
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    
    now = datetime.datetime.now()
    future = now + datetime.timedelta(hours=24)
    
    rows = c.execute("SELECT id, event, due_date, due_time FROM tasks WHERE reminded = 0").fetchall()
    
    if not rows:
        print("📭 当前没有未提醒的任务。")
        conn.close()
        return
    
    for row in rows:
        task_id, event, date, time = row
        due_str = f"{date} {time}"
        try:
            due_dt = datetime.datetime.strptime(due_str, "%Y-%m-%d %H:%M")
        except ValueError:
            due_dt = datetime.datetime.strptime(f"{date} {time}:00", "%Y-%m-%d %H:%M:%S")
        
        if now <= due_dt <= future:
            message = f"📢 任务「{event}」即将在 {due_str} 截止！"
            send_desktop_notification("DDL 提醒器", message)
            send_pushplus("DDL 即将到期", message)
            c.execute("UPDATE tasks SET reminded = 1 WHERE id = ?", (task_id,))
            print(f"⏰ 已提醒（即将到期）: {event}")
        elif due_dt < now:
            message = f"🚨 任务「{event}」原定于 {due_str} 截止，已经过期！"
            send_desktop_notification("DDL 提醒器", message)
            send_pushplus("DDL 已过期", message)
            c.execute("UPDATE tasks SET reminded = 1 WHERE id = ?", (task_id,))
            print(f"⏰ 已提醒（已过期）: {event}")
        else:
            print(f"⏳ {event} 截止于 {due_str}，不在24小时内，暂不提醒")
    
    conn.commit()
    conn.close()
    print("✅ 检查完成")

if __name__ == "__main__":
    # 如果本地没有设置环境变量，可以添加 fallback（本地测试用）
    if not PUSHPLUS_TOKEN:
        # 尝试从 .env 加载（仅限本地开发）
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            env_path = Path(__file__).parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
                PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")
                print("✅ 从 .env 文件加载了 PUSHPLUS_TOKEN")
        except ImportError:
            pass  # 云端可能没有 dotenv，忽略
    
    check_and_remind()