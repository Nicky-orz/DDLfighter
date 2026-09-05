import os
import sqlite3
from datetime import datetime
from icalendar import Calendar, Event
import pytz

# ---------- 锁定工作目录 ----------
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def export_to_ics():
    """从数据库读取任务，生成 .ics 日历文件"""
    
    # 1. 连接数据库，读取所有未提醒的任务（你也可以改成所有任务）
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    rows = c.execute(
        "SELECT id, event, due_date, due_time, reminded FROM tasks WHERE reminded = 0 ORDER BY due_date, due_time"
    ).fetchall()
    conn.close()
    
    if not rows:
        print("📭 当前没有待办任务，无需导出。")
        return
    
    # 2. 创建日历容器
    cal = Calendar()
    cal.add('prodid', '-//DDL Fighter//CN//')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    
    # 设置时区（北京时间）
    tz = pytz.timezone('Asia/Shanghai')
    
    # 3. 遍历任务，生成日历事件
    for row in rows:
        task_id, event, due_date, due_time, reminded = row
        
        # 拼接日期时间字符串
        due_str = f"{due_date} {due_time}"
        try:
            # 解析时间并赋予时区
            dt = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
            dt = tz.localize(dt)
        except ValueError:
            # 如果时间格式不标准，尝试补秒数
            dt = datetime.strptime(f"{due_date} {due_time}:00", "%Y-%m-%d %H:%M:%S")
            dt = tz.localize(dt)
        except Exception as e:
            print(f"⚠️ 任务 ID:{task_id} 时间解析失败，跳过: {e}")
            continue
        
        # 创建单个事件
        ical_event = Event()
        ical_event.add('summary', f'📌 {event}')
        ical_event.add('dtstart', dt)
        ical_event.add('dtend', dt)  # 截止时间作为结束时间（瞬间事件）
        ical_event.add('description', f'由 DDL Fighter 自动导出 (ID: {task_id})\n原始内容: 略')
        
        # 添加提醒（提前30分钟，手机系统日历会识别）
        ical_event.add('x-apple-alarm', '0; -30')  # 苹果系
        ical_event.add('alarm', {
            'trigger': '-PT30M',  # 标准 iCalendar 提醒：提前30分钟
            'action': 'DISPLAY',
            'description': f'📢 任务 {event} 即将截止！'
        })
        
        cal.add_component(ical_event)
    
    # 4. 写入 .ics 文件
    output_path = os.path.abspath('tasks.ics')
    with open(output_path, 'wb') as f:
        f.write(cal.to_ical())
    
    print(f"✅ 导出成功！共导出 {len(rows)} 个任务到：")
    print(f"   {output_path}")
    print("\n📱 请将此文件发送到手机，用「日历」应用打开即可导入。")

if __name__ == "__main__":
    print("="*50)
    print("        📅 导出日历文件 (.ics)")
    print("="*50)
    export_to_ics()