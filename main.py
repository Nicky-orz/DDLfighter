import os
import json
import sqlite3
from datetime import datetime
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
    print("✅ 数据库初始化完成 (tasks.db)")

# ---------- 3. AI 批量提取函数（支持多事件） ----------
def extract_events(content):
    """调用AI提取所有事件，返回列表"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": f"今天是{today}。你是一个日程提取助手。从用户输入中提取**所有**事件名称和截止时间。如果日期是中文（如'下周三'），转换为YYYY-MM-DD格式。**只返回合法的JSON列表，必须使用双引号**。格式：[{{\"事件\":\"\",\"日期\":\"YYYY-MM-DD\",\"时间\":\"HH:MM\"}}]。如果没有提取到任何事件，返回空列表[]。"},
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

# ---------- 4. 存入本地数据库 ----------
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

# ---------- 5. 主流程 ----------
if __name__ == "__main__":
    init_db()
    
    print("="*50)
    print("       群通知智能提取 (支持批量多事件)")
    print("="*50)
    
    content = input("\n请将群通知粘贴到这里，然后按回车：\n")
    
    try:
        events = extract_events(content)
        
        if not events:
            print("\n📭 未提取到任何有效事件，请检查内容是否包含日期和任务。")
        else:
            print(f"\n📅 提取到 {len(events)} 个事件：")
            for idx, evt in enumerate(events, 1):
                print(f"  {idx}. {evt['事件']} | {evt['日期']} {evt['时间']}")
                save_to_db(evt["事件"], evt["日期"], evt["时间"], content)
            
            print(f"\n✅ 全部 {len(events)} 个任务已保存到本地数据库！")
    
    except Exception as e:
        print(f"\n⚠️ 处理失败: {e}")