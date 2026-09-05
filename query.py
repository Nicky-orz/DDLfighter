import sqlite3

conn = sqlite3.connect('tasks.db')
rows = conn.execute("SELECT id, event, due_date, due_time, reminded FROM tasks").fetchall()
conn.close()

print("📋 所有任务:")
for row in rows:
    print(f"  ID:{row[0]} | {row[1]} | 截止: {row[2]} {row[3]} | 已提醒: {row[4]}")