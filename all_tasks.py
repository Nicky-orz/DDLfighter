import sqlite3
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print(f"📁 当前工作目录: {os.getcwd()}")
print(f"📁 数据库文件路径: {os.path.abspath('tasks.db')}")

conn = sqlite3.connect('tasks.db')
c = conn.cursor()

rows = c.execute("""
    SELECT id, event, due_date, due_time, reminded, created_at 
    FROM tasks 
    ORDER BY due_date ASC, due_time ASC
""").fetchall()

print(f"📊 数据库中共有 {len(rows)} 条记录")

for row in rows:
    print(row)

conn.close()