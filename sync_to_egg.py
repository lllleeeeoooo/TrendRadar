import sqlite3
import requests
import os
import json
import glob

def get_latest_db(directory="output/news"):
    """自动获取目录下最新生成的 .db 文件路径"""
    # 查找目录下所有的 .db 文件
    search_pattern = os.path.join(directory, "*.db")
    db_files = glob.glob(search_pattern)

    if not db_files:
        return None

    # 按文件的修改时间排序，拿到最新生成的一个
    latest_db = max(db_files, key=os.path.getmtime)
    return latest_db

def sync_data():
    api_url = os.environ.get('EGG_API_URL')
    api_token = os.environ.get('EGG_API_TOKEN')

    if not api_url:
        print("未配置 EGG_API_URL，跳过同步步骤。")
        return

    # 1. 动态获取最新的数据库文件
    db_path = get_latest_db()

    if not db_path:
        print("在 output/news/ 目录下未找到任何 .db 文件，暂无数据同步。")
        return

    print(f"找到最新数据库文件: {db_path}，准备读取...")

    # 2. 读取 SQLite 数据库
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 转化为字典(Dict)格式
        cursor = conn.cursor()

        # 读取数据 (请确保表名正确，这里假设是 articles)
        cursor.execute("SELECT * FROM news_items")
        rows = cursor.fetchall()

        data_to_send = [dict(row) for row in rows]
        conn.close()
    except Exception as e:
        print(f"读取数据库出错: {str(e)}")
        return

    if not data_to_send:
        print("数据库内没有数据，无需同步。")
        return

    # 3. 发送数据到 Egg.js 服务器
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        "data": data_to_send
    }

    try:
        print(f"正在向 {api_url} 同步 {len(data_to_send)} 条数据...")
        response = requests.post(api_url, json=payload, headers=headers)
        print("服务器响应状态码:", response.status_code)
        print("服务器响应内容:", response.text)
    except Exception as e:
        print("同步失败，请求报错:", str(e))

if __name__ == "__main__":
    sync_data()
