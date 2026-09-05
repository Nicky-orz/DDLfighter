import sqlite3
import os
import re
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------- 辅助函数 ----------
def show_tasks():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    rows = c.execute(
        "SELECT id, event, due_date, due_time, reminded FROM tasks ORDER BY id"
    ).fetchall()
    conn.close()
    
    if not rows:
        print("📭 数据库为空。")
        return []
    
    print("\n" + "="*70)
    print("当前所有任务：")
    print("="*70)
    for r in rows:
        status = "⏳ 待提醒" if r[4] == 0 else "✅ 已提醒"
        event_display = r[1][:25] + "..." if len(r[1]) > 25 else r[1]
        print(f"  ID:{r[0]:2d} | {status} | {event_display} | 截止: {r[2]} {r[3]}")
    print("="*70)
    return rows

def parse_id_list(input_str):
    """
    解析用户输入的ID列表，支持逗号分隔和范围
    例如: "1,3,5" → [1,3,5]
          "1-5" → [1,2,3,4,5]
          "1,3-5,7" → [1,3,4,5,7]
    """
    ids = []
    parts = input_str.replace(' ', '').split(',')
    for part in parts:
        if '-' in part:
            start, end = part.split('-')
            start, end = int(start), int(end)
            if start > end:
                start, end = end, start
            ids.extend(range(start, end+1))
        else:
            if part.isdigit():
                ids.append(int(part))
    return sorted(set(ids))

def get_task_by_id(task_id):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    row = c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row

def update_task(task_id, field, value):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    if field == 'due_date':
        c.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (value, task_id))
    elif field == 'due_time':
        c.execute("UPDATE tasks SET due_time = ? WHERE id = ?", (value, task_id))
    elif field == 'reminded':
        c.execute("UPDATE tasks SET reminded = ? WHERE id = ?", (value, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# ---------- 主交互 ----------
def edit_task():
    while True:
        rows = show_tasks()
        if not rows:
            input("\n按回车键返回...")
            return
        
        print("\n操作菜单：")
        print("  1 - 修改单个任务（日期/时间）")
        print("  2 - 重置单个任务提醒状态")
        print("  3 - 删除单个任务")
        print("  4 - 批量操作（重置状态 / 删除 / 改日期）")
        print("  0 - 退出")
        
        choice = input("\n请选择操作（输入数字）：").strip()
        
        if choice == "0":
            print("👋 退出编辑工具。")
            break
        
        if choice not in ["1", "2", "3", "4"]:
            print("⚠️ 无效选项，请重新输入。")
            continue
        
        # ---------- 单个任务操作 ----------
        if choice in ["1", "2", "3"]:
            try:
                task_id = int(input("请输入任务 ID（输入 0 返回菜单）：").strip())
            except ValueError:
                print("⚠️ 请输入有效数字。")
                continue
            if task_id == 0:
                continue
            existing = get_task_by_id(task_id)
            if not existing:
                print(f"⚠️ 未找到 ID 为 {task_id} 的任务。")
                continue
            
            if choice == "1":
                # 修改日期/时间（与之前相同）
                print(f"\n当前任务：{existing[1]} | {existing[2]} {existing[3]}")
                print("修改选项：a-改日期  b-改时间  c-同时改")
                sub = input("请选择 (a/b/c)：").strip().lower()
                new_date, new_time = existing[2], existing[3]
                if sub == "a":
                    new_date = input("新日期 (YYYY-MM-DD)：").strip()
                elif sub == "b":
                    new_time = input("新时间 (HH:MM)：").strip()
                elif sub == "c":
                    new_date = input("新日期 (YYYY-MM-DD)：").strip()
                    new_time = input("新时间 (HH:MM)：").strip()
                else:
                    print("⚠️ 无效选项")
                    continue
                update_task(task_id, 'due_date', new_date)
                update_task(task_id, 'due_time', new_time)
                print(f"✅ 已更新任务 ID:{task_id}")
            
            elif choice == "2":
                current = existing[4]
                new = 1 if current == 0 else 0
                update_task(task_id, 'reminded', new)
                print(f"✅ 任务 ID:{task_id} 状态已切换为 {'已提醒' if new else '待提醒'}")
            
            elif choice == "3":
                confirm = input(f"⚠️ 确定删除任务「{existing[1]}」？(y/n)：").strip().lower()
                if confirm == 'y':
                    delete_task(task_id)
                    print(f"✅ 已删除任务 ID:{task_id}")
                else:
                    print("⏭️ 取消删除。")
        
        # ---------- 批量操作 ----------
        elif choice == "4":
            print("\n批量操作选项：")
            print("  a - 批量重置提醒状态（待办↔已提醒）")
            print("  b - 批量删除任务")
            print("  c - 批量修改截止日期（统一为同一天）")
            print("  d - 批量修改截止时间（统一为同一时刻）")
            sub = input("请选择 (a/b/c/d)：").strip().lower()
            
            if sub not in ['a', 'b', 'c', 'd']:
                print("⚠️ 无效选项。")
                continue
            
            id_input = input("请输入任务 ID 列表（支持逗号分隔和范围，如 1,3-5,7）：").strip()
            ids = parse_id_list(id_input)
            if not ids:
                print("⚠️ 未解析到有效 ID。")
                continue
            
            # 验证所有 ID 是否存在
            valid_ids = []
            for tid in ids:
                if get_task_by_id(tid):
                    valid_ids.append(tid)
                else:
                    print(f"⚠️ ID {tid} 不存在，已忽略。")
            if not valid_ids:
                print("⚠️ 没有有效的 ID。")
                continue
            
            # 显示将要操作的任务列表
            conn = sqlite3.connect('tasks.db')
            c = conn.cursor()
            placeholders = ','.join('?' * len(valid_ids))
            rows = c.execute(f"SELECT id, event, due_date, due_time, reminded FROM tasks WHERE id IN ({placeholders})", valid_ids).fetchall()
            conn.close()
            
            print("\n将要操作的任务：")
            for r in rows:
                status = "待提醒" if r[4] == 0 else "已提醒"
                print(f"  ID:{r[0]:2d} | {r[1]} | 截止: {r[2]} {r[3]} | {status}")
            
            confirm = input("\n确认执行批量操作？(y/n)：").strip().lower()
            if confirm != 'y':
                print("⏭️ 取消操作。")
                continue
            
            # 执行批量操作
            if sub == 'a':
                # 批量切换提醒状态（将所有选中的任务切换到相反状态）
                for tid in valid_ids:
                    row = get_task_by_id(tid)
                    new = 1 if row[4] == 0 else 0
                    update_task(tid, 'reminded', new)
                print(f"✅ 已切换 {len(valid_ids)} 个任务的提醒状态。")
            
            elif sub == 'b':
                for tid in valid_ids:
                    delete_task(tid)
                print(f"✅ 已删除 {len(valid_ids)} 个任务。")
            
            elif sub == 'c':
                new_date = input("请输入统一的日期 (YYYY-MM-DD)：").strip()
                if len(new_date) != 10 or new_date[4] != '-' or new_date[7] != '-':
                    print("⚠️ 日期格式错误。")
                    continue
                for tid in valid_ids:
                    update_task(tid, 'due_date', new_date)
                print(f"✅ 已修改 {len(valid_ids)} 个任务的截止日期为 {new_date}。")
            
            elif sub == 'd':
                new_time = input("请输入统一的时间 (HH:MM)：").strip()
                if len(new_time) != 5 or new_time[2] != ':':
                    print("⚠️ 时间格式错误。")
                    continue
                for tid in valid_ids:
                    update_task(tid, 'due_time', new_time)
                print(f"✅ 已修改 {len(valid_ids)} 个任务的截止时间为 {new_time}。")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    print("="*50)
    print("        📝 任务编辑工具（支持批量操作）")
    print("="*50)
    edit_task()