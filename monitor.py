import os
import json
import sqlite3
import pyperclip
from time import sleep
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------- 1. 加载环境变量 ----------
script_dir = Path(__file__).parent
load_dotenv(script_dir / '.env')

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ---------- 2. 初始化本地数据库 ----------
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
    print("✅ 数据库已就绪 (tasks.db)")

# ---------- 3. 时间规范化（修复 24:00 问题） ----------
def normalize_time(date_str, time_str):
    """
    将 24:00 转换为次日 00:00
    例如: 2026-09-09 24:00 → 2026-09-10 00:00
    """
    if time_str == "24:00":
        dt = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)
        return dt.strftime("%Y-%m-%d"), "00:00"
    # 如果时间带有秒数（如 14:00:00），截断为 HH:MM
    if len(time_str) > 5 and time_str[2] == ':' and time_str[5] == ':':
        time_str = time_str[:5]
    return date_str, time_str

# ---------- 4. AI 批量提取函数 ----------
def extract_events(content):
    """调用AI提取所有事件，返回列表"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": f"今天是{today}。你是一个日程提取助手。从用户输入中提取**所有**事件名称和截止时间。如果日期是中文（如'下周三'），转换为YYYY-MM-DD格式。**只返回合法的JSON列表，必须使用双引号**。格式：[{{\"事件\":\"\",\"日期\":\"YYYY-MM-DD\",\"时间\":\"HH:MM\"}}]。如果时间包含秒数，只保留到分钟。如果没有提取到任何事件，返回空列表[]。"},
            {"role": "user", "content": content}
        ],
        temperature=0.1
    )
    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return [data]
        return data
    except json.JSONDecodeError:
        print(f"⚠️ AI返回非JSON格式: {raw}")
        return []

# ---------- 5. 存入本地数据库 ----------
def save_to_db(event, date, time, raw_text):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (event, due_date, due_time, raw_text) VALUES (?, ?, ?, ?)",
        (event, date, time, raw_text)
    )
    conn.commit()
    conn.close()
    print(f"  ✅ 已存入: {event} | {date} {time}")

# ---------- 6. 监控主循环 ----------
def main():
    init_db()
    
    print("="*50)
    print("   📋 剪贴板监控已启动（支持批量多事件）")
    print("   复制群通知后，在终端输入 y 确认提取，输入 n 忽略")
    print("   按 Ctrl+C 可随时退出监控")
    print("="*50)
    
    last_content = ""
    
    while True:
        sleep(1.5)  # ← 使用 sleep() 而非 time.sleep()
        current = pyperclip.paste()
        
        if current and current != last_content:
            # 预览（分行显示）
            lines = current.splitlines()
            if len(lines) > 5:
                preview = "\n   ".join(lines[:5]) + "\n   ...(还有更多行)"
            else:
                preview = "\n   ".join(lines)
            
            print("\n📌 检测到新复制内容：")
            print(f"   {preview}")
            
            choice = input("是否提取？(y=确认提取 / n=忽略 / q=退出监控): ").strip().lower()
            
            if choice == 'q':
                print("👋 已退出监控程序。")
                break
            elif choice == 'y':
                print("🤖 正在调用AI提取（支持多事件）...")
                try:
                    events = extract_events(current)
                    
                    if not events:
                        print("📭 AI未提取到任何有效事件，请检查内容是否包含日期和任务。")
                    else:
                        print(f"📅 提取到 {len(events)} 个事件，正在入库...")
                        for idx, evt in enumerate(events, 1):
                            # 时间规范化：修复 24:00 问题
                            date, time = normalize_time(evt["日期"], evt["时间"])
                            print(f"  {idx}. {evt['事件']} | {date} {time}")
                            save_to_db(evt["事件"], date, time, current)
                        print(f"✅ 全部 {len(events)} 个任务已保存！")
                except Exception as e:
                    print(f"❌ 提取失败: {e}")
            else:
                print("⏭️ 已忽略此内容。")
            
            last_content = current

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 监控已手动停止。")