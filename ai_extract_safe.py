import os
import json
import ast
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# 关键修复：获取当前脚本所在的目录，拼接 .env 绝对路径
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(env_path)  # 显式指定绝对路径

# 可选：加一行调试，确认是否读到（跑通后可以删掉）
print(f"正在加载环境变量: {env_path}，是否存在: {env_path.exists()}")

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

print("="*40)
print("       群通知智能提取工具 (修复版)")
print("="*40)
content = input("\n请将群通知粘贴到这里，然后按回车：\n")

response = client.chat.completions.create(
    model="deepseek-chat",  # 或 "Qwen/Qwen2.5-7B-Instruct"
    messages=[
        {"role": "system", "content": "你是一个日程提取助手。从用户输入中提取事件名称和截止时间。如果日期是中文（如'下周三'），转换为YYYY-MM-DD格式。**只返回合法的JSON，必须使用双引号，不要有任何额外文字**。格式：{\"事件\":\"\",\"日期\":\"YYYY-MM-DD\",\"时间\":\"HH:MM\"}"},
        {"role": "user", "content": content}
    ],
    temperature=0.1
)

raw = response.choices[0].message.content
print("\n【原始返回内容】")
print(raw)

# 尝试解析JSON，如果失败则尝试将单引号转为双引号（兼容Python字典）
try:
    result = json.loads(raw)
except json.JSONDecodeError:
    # 尝试用 ast.literal_eval 解析 Python 字典
    try:
        result = ast.literal_eval(raw)
    except Exception as e:
        print(f"\n⚠️ 无法解析返回内容：{e}")
        print("原始内容：", raw)
        exit()

print("\n【提取结果】")
print(json.dumps(result, ensure_ascii=False, indent=2))
print("="*40)
print("\n✅ 提取成功！")